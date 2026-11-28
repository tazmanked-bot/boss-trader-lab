"""Read-only metrics from an explicitly owner-supplied consistent SQLite snapshot.

Never opens a configured live recorder, runs backup/checkpoint, or changes a DB.
"""
import json
from pathlib import Path
import re
import sqlite3
from research import llama_analyst_033 as adapter

MAX_ROWS=10000
MAX_DB_BYTES=2*1024**3


def need(value,reason):
    if not value:raise adapter.Refused(reason)


def identifier(value):
    need(type(value) is str and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}',value),'SQL_IDENTIFIER_INVALID')
    return '"'+value+'"'


def freshness(snapshot,table,open_column,ingest_column,as_of,*,snapshot_kind,stream_column=None,stream_value=None,max_ingest_age=7200,expected_interval=3600):
    need(snapshot_kind=='OWNER_CONSISTENT_OFFLINE_SNAPSHOT','CONSISTENT_SNAPSHOT_REQUIRED')
    need(type(as_of) is int and 946684800<=as_of<4102444800,'AS_OF_SECONDS_REQUIRED')
    need(type(max_ingest_age) is int and 0<max_ingest_age<=86400 and expected_interval==3600,'TIME_POLICY_INVALID')
    path=Path(snapshot)
    need(path.is_absolute() and not path.is_symlink() and path.is_file(),'SNAPSHOT_FILE_REQUIRED')
    need(not any((Path(str(path)+suffix).exists() or Path(str(path)+suffix).is_symlink()) for suffix in ('-wal','-shm','-journal')),'SIDECAR_PRESENT_LIVE_OR_INCOMPLETE_SNAPSHOT')
    before=path.stat();need(0<before.st_size<=MAX_DB_BYTES,'SNAPSHOT_SIZE')
    table,opening,ingest=map(identifier,(table,open_column,ingest_column))
    stream=identifier(stream_column)
    need(type(stream_value) is str and re.fullmatch('[A-Za-z0-9/_-]{1,40}',stream_value),'EXACT_STREAM_FILTER_REQUIRED')
    # immutable=1 is safe ONLY for the declared static, single-file snapshot.
    # It would be misleading/unsafe for a live WAL database: that is refused above.
    connection=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=1)
    try:
        connection.enable_load_extension(False)
        connection.execute('PRAGMA temp_store=MEMORY');connection.execute('PRAGMA query_only=ON');connection.execute('PRAGMA trusted_schema=OFF')
        budget=[0]
        def progress():
            budget[0]+=1;return 1 if budget[0]>1000 else 0
        connection.set_progress_handler(progress,1000)
        rows=connection.execute(f'SELECT {opening},{ingest} FROM {table} WHERE {stream} = ? ORDER BY {ingest} DESC,{opening} DESC LIMIT ?', (stream_value,MAX_ROWS+1)).fetchall()
    except sqlite3.DatabaseError:raise adapter.Refused('READ_ONLY_QUERY_REFUSED_SCHEMA_OR_BUDGET') from None
    finally:connection.close()
    after=path.stat()
    need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'SNAPSHOT_CHANGED')
    need(bool(rows),'SNAPSHOT_EMPTY')
    truncated=len(rows)>MAX_ROWS;rows=rows[:MAX_ROWS]
    for opened,recorded in rows:
        need(type(opened) is int and type(recorded) is int and 946684800<=opened<4102444800
             and opened%3600==0 and opened+3600<=recorded<=as_of,'TIMESTAMP_OR_INGEST_SEMANTICS_INVALID')
    closes=sorted(set(o+3600 for o,_ in rows));ingestions=sorted(set(t for _,t in rows))
    history_gaps=[{'after_close':a,'before_close':b,'missing_hours':(b-a)//3600-1} for a,b in zip(closes,closes[1:]) if b-a>3600]
    record_gaps=[{'after_record':a,'before_record':b,'seconds':b-a} for a,b in zip(ingestions,ingestions[1:]) if b-a>max_ingest_age]
    last_ingest=ingestions[-1];last_close=closes[-1]
    return {'state':'READ_ONLY_SNAPSHOT_METRICS_NOT_LIVE_SERVICE_HEALTH','rows_examined':len(rows),
            'history_scope':f'LATEST_{MAX_ROWS}_INGESTIONS_ONLY' if truncated else 'SNAPSHOT_ROWS_ONLY',
            'stream_filter':stream_value,'as_of':as_of,'latest_recorded_at':last_ingest,'latest_candle_close':last_close,
            'ingest_age_seconds':as_of-last_ingest,'candle_age_seconds':as_of-last_close,
            'freshness':'RECENT_RELATIVE_TO_SUPPLIED_AS_OF' if as_of-last_ingest<=max_ingest_age and as_of-last_close<3600 else 'STALE',
            'historical_candle_gaps':history_gaps,'observed_recording_gaps':record_gaps,
            'possible_delayed_or_backfilled_rows':sum(t-(o+3600)>max_ingest_age for o,t in rows),
            'outage_cause':'NOT_ESTABLISHED','ingest_column_semantics':'OWNER_DECLARED_ACTUAL_INSERT_TIME_NOT_AUTHENTICATED',
            'backfill_vs_outage':'HISTORY_GAPS_AND_INSERT_GAPS_ARE_DIFFERENT; NO AUTOMATIC_BACKFILL',
            'database_writes':0,'service_operations':0}


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot');parser.add_argument('--table');parser.add_argument('--open-column');parser.add_argument('--ingest-column')
    parser.add_argument('--stream-column');parser.add_argument('--stream-value')
    parser.add_argument('--as-of',type=int);parser.add_argument('--snapshot-kind')
    args=parser.parse_args()
    if not args.snapshot:
        print('Idle: no recorder or database accessed.');return
    print(json.dumps(freshness(args.snapshot,args.table,args.open_column,args.ingest_column,args.as_of,snapshot_kind=args.snapshot_kind,stream_column=args.stream_column,stream_value=args.stream_value),indent=2))


if __name__=='__main__':main()
