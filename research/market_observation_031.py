"""Manual local Binance BTC/USDT observation; no reversal admission or orders."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

from boss_trader_lab import BINANCE_KLINES, MAX_CANDLES, observe
from research.dashboard_029 import generate

SYMBOL='BTCUSDT'
URL=BINANCE_KLINES+'?symbol=BTCUSDT&interval=1h&limit='+str(MAX_CANDLES)
BODY_LIMIT=65536
OUTPUT_LIMIT=8192
SOCKET_TIMEOUT=12
WORKER_TIMEOUT=15
COOLDOWN=30
HOUR=3600000


def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()


def decode(raw):
    if len(raw)>BODY_LIMIT:raise ValueError('Provider response exceeds 65536 bytes')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def parse(raw,now_ms):
    rows=decode(raw)
    if type(now_ms) is not int or now_ms<=0:raise ValueError('Invalid capture clock')
    if not isinstance(rows,list) or not 22<=len(rows)<=MAX_CANDLES:raise ValueError('Expected 22–30 Binance spot klines')
    completed=[];previous=None
    for row in rows:
        if not isinstance(row,list) or len(row)!=12:raise ValueError('Expected exact 12-field kline')
        opened,closed=row[0],row[6]
        if type(opened) is not int or type(closed) is not int or opened%HOUR or closed!=opened+HOUR-1:raise ValueError('Invalid hourly boundaries')
        if previous is not None and opened!=previous+HOUR:raise ValueError('Duplicate, unordered or gapped candles')
        previous=opened
        if opened>now_ms:raise ValueError('Future candle')
        values=[]
        for index in (1,2,3,4,5,7,9,10):
            value=row[index]
            if not isinstance(value,str) or len(value)>64:raise ValueError('Invalid numeric field')
            try:number=Decimal(value)
            except InvalidOperation:raise ValueError('Invalid decimal') from None
            if not number.is_finite() or number<0 or (index in (1,2,3,4) and number<=0):raise ValueError('Invalid price or volume')
            if not math.isfinite(float(number)):raise ValueError('Numeric overflow')
            values.append(number)
        o,h,l,c,v,q,buy,buyq=values
        if not l<=min(o,c)<=max(o,c)<=h or buy>v or buyq>q:raise ValueError('Inconsistent OHLC/volume')
        if type(row[8]) is not int or row[8]<0 or row[11]!='0':raise ValueError('Invalid trade count/reserved field')
        if (v==0)!=(q==0) or (v==0 and row[8]!=0):raise ValueError('Inconsistent zero volume')
        if closed<now_ms:completed.append((row,float(c)))
    if len(completed)<21:raise ValueError('Insufficient completed hourly candles')
    latest=completed[-1][0]
    age=now_ms-(latest[6]+1)
    if age<0 or age>=HOUR:raise ValueError('Latest completed hourly candle stale or future')
    result=observe(SYMBOL,[v for _,v in completed])
    # Output close-only observations; full rows never cross the UI boundary.
    return {'source':'BINANCE_PUBLIC_SPOT','pair':'BTC/USDT','quote':'USDT','endpoint':URL,
            'status':'OBSERVE_ONLY','interval':'1h','capture_time':utc(now_ms),
            'latest_completed_close_time':utc(latest[6]+1),'latest_completed_close':latest[4],
            'freshness':'RECENT_RELATIVE_TO_UNVERIFIED_LOCAL_CLOCK','clock':'LOCAL_SYSTEM_UTC_UNVERIFIED_B4_NO_GO',
            'current_executable_quote':None,'completed_count':len(completed),
            'change_last_bar_pct':result['change_last_bar_pct'],
            'reversal_classification':'UNAVAILABLE_SOURCE_ADMISSION_HOLD','paper_recording':'UNAVAILABLE_OBSERVATION_SOURCE',
            'trading_authority':'NONE'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Provider redirect refused')


def fetch_once(opener=None,clock=time.time):
    opener=opener or build_opener(NoRedirect)
    request=Request(URL,headers={'User-Agent':'boss-trader-lab-research/0.1','Accept':'application/json','Accept-Encoding':'identity'})
    with opener.open(request,timeout=SOCKET_TIMEOUT) as response:
        if response.status!=200:raise ValueError('Provider HTTP '+str(response.status))
        if response.geturl()!=URL:raise ValueError('Unexpected provider URL')
        if response.headers.get('Content-Type','').split(';')[0].strip()!='application/json':raise ValueError('Expected JSON response content type')
        if response.headers.get('Content-Length') is not None and (not response.headers['Content-Length'].isdigit() or int(response.headers['Content-Length'])>BODY_LIMIT):raise ValueError('Provider declared body too large or invalid')
        if response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Compressed response refused')
        raw=response.read(BODY_LIMIT+1)
    return parse(raw,int(clock()*1000))


class ProviderRefusal(ValueError):
    def __init__(self,message,retry_after=0):
        super().__init__(message);self.retry_after=retry_after


def retry_delay(error):
    value=error.headers.get('Retry-After','') if error.headers else ''
    # Numeric seconds only. Unknown/date or enormous values effectively pause
    # this runner until an explicit owner restart; never shorten a long cooldown.
    if value.isdigit() and len(value)<=12:return max(120,int(value))
    return 10**15 if value else 120


def worker_result():
    """One disposable child, one fixed public GET; no retries or fallback."""
    try:
        run=subprocess.run([sys.executable,'-B','-m','research.market_observation_031','--worker'],
                           capture_output=True,timeout=WORKER_TIMEOUT,check=False)
    except subprocess.TimeoutExpired:raise ValueError('Observation worker exceeded 15-second wait budget') from None
    if len(run.stdout)>OUTPUT_LIMIT or run.returncode:raise ValueError('Observation worker failed or output exceeded limit')
    result=json.loads(run.stdout)
    if not isinstance(result,dict):raise ValueError('Invalid worker result')
    if 'error' in result:raise ProviderRefusal(result['error'],result.get('retry_after',0))
    return result


class Service:
    def __init__(self,fetch=worker_result,clock=time.monotonic):
        self.fetch=fetch;self.clock=clock;self.lock=threading.Lock();self.last=None;self.hold_until=0
    def refresh(self):
        if not self.lock.acquire(blocking=False):return 409,{'error':'Refresh already running'}
        try:
            now=self.clock()
            if now<self.hold_until:return 429,{'error':'Provider cooldown active; wait before manual Refresh','retry_after':math.ceil(self.hold_until-now)}
            if self.last is not None and now-self.last<COOLDOWN:return 429,{'error':'Wait 30 seconds between manual refresh attempts'}
            self.last=now
            try:return 200,self.fetch()
            except ProviderRefusal as exc:
                if exc.retry_after:
                    self.hold_until=self.clock()+max(COOLDOWN,exc.retry_after)
                    return 429,{'error':str(exc)[:300],'retry_after':exc.retry_after}
                return 502,{'error':str(exc)[:300]}
            except Exception as exc:return 502,{'error':str(exc)[:300] or type(exc).__name__}
        finally:self.lock.release()


def handler(html,service):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup();self.connection.settimeout(5)
        def log_message(self,*args):pass
        def send(self,status,body,kind='application/json'):
            raw=body.encode() if isinstance(body,str) else json.dumps(body,allow_nan=False).encode()
            if len(raw)>512*1024:status=500;raw=b'{"error":"Local response too large"}'
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY')
            self.send_header('Connection','close');self.end_headers();self.wfile.write(raw);self.close_connection=True
        def permitted(self,post=False):
            expected='127.0.0.1:'+str(self.server.server_port)
            if self.headers.get_all('Host')!=[expected]:return False
            origins=self.headers.get_all('Origin') or []
            if origins and origins!=['http://'+expected]:return False
            if post and origins!=['http://'+expected]:return False
            if self.headers.get('Sec-Fetch-Site') not in (None,'same-origin','none'):return False
            return True
        def do_GET(self):
            if not self.permitted():return self.send(403,{'error':'Host/Origin refused'})
            if self.path!='/':return self.send(404,{'error':'Fixed local routes only'})
            self.send(200,html,'text/html')
        def do_POST(self):
            if not self.permitted(True):return self.send(403,{'error':'Host/Origin refused'})
            if self.path!='/api/market-read':return self.send(404,{'error':'Fixed market route only'})
            if self.headers.get_all('Content-Length')!=['2'] or self.headers.get('Transfer-Encoding') is not None or self.headers.get_all('Content-Type')!=['application/json']:return self.send(400,{'error':'Expected exact empty JSON object'})
            if self.rfile.read(2)!=b'{}':return self.send(400,{'error':'No symbols, URLs or extra fields accepted'})
            status,result=service.refresh();self.send(status,result)
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve',action='store_true');parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    if args.worker:
        try:out=fetch_once()
        except HTTPError as exc:out={'error':'Provider HTTP '+str(exc.code)+'; no retry','retry_after':retry_delay(exc) if exc.code in (418,429) else 0}
        except Exception as exc:out={'error':type(exc).__name__+': '+str(exc)[:220]}
        print(json.dumps(out,allow_nan=False));return
    if not args.serve:
        print('Offline default: no server or market requests. Use --serve for manual local observation.');return
    if not 1024<=args.port<=65535:parser.error('port must be 1024–65535')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(generate(),Service()))
    server.daemon_threads=True
    print(f'Open http://127.0.0.1:{args.port}/ — explicit Refresh only; OBSERVE_ONLY; NO ORDERS',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
