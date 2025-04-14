import {ShardingTest} from 'jstests/libs/shardingtest.js';

const st = new ShardingTest({shards: 2});

jsTest.log('sleeping');
sleep(100000000000);

st.stop();
