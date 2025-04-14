import {ShardingTest} from 'jstests/libs/shardingtest.js';

const st = new ShardingTest({shards: 2});

const kCollName = 'coll';
const kDbName = 'test';
const kNs1 = 'test.' + kCollName
const nDocs = 100;
const primaryShard = st.shard0.shardName;

// Set primary shard
assert.commandWorked(
    st.s.adminCommand({enableSharding: kDbName, primaryShard: primaryShard}));

// Shard kNs1
assert.commandWorked(
    st.s.adminCommand({shardCollection: kNs1, key: {x: 1}, unique: false}));

// Insert nDocs {x:i}
for (let i = 0; i < nDocs; i++) {
  assert.commandWorked(
      st.s.getDB('test').getCollection(kCollName).insertOne({x: i}))
}

assert.eq(
    nDocs, st.s.getDB('test').getCollection(kCollName).countDocuments({}));

// Equally distribute
jsTest.log('migration');
assert.commandWorked(st.s.adminCommand({
  moveRange: kNs1,
  min: {x: MinKey},
  max: {x: nDocs / 2},
  toShard: st.shard1.shardName
}));
jsTest.log('migration completed');

jsTest.log('sleeping');
sleep(100000000000);

st.stop();
