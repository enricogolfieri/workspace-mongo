use('test');
// create a collection && insert some documents
// create an index
db.bigdata.createIndex({x: 1});

// shard the collection
sh.shardCollection("test.bigdata", {x: 1});

// insert some data
var bulk = db.bigdata.initializeUnorderedBulkOp();
var oneMb = 1024 * 1024 / 4;  // int32
for (var i = 0; i < oneMb; i++) {
    bulk.insert({x: i});
}
bulk.execute();
