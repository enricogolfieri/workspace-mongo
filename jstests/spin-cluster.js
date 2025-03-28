import {ShardingTest} from 'jstests/libs/shardingtest.js';

var st = new ShardingTest({shards: 1});

jsTest.log('sleeping');
sleep(100000000000);

st.stop();
