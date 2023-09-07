/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

/*
Proves a bug that we don't target shards that do not hold chunks in drop index. This will result in
invalid data which instaead checks all the shards
*/

const database = 'db';
const collection = 'points';

// Create a new database.
use(database);

// Create a new collection.
db.points.drop();
db.adminCommand({movePrimary: database, to: "shard01"});
db.createCollection(collection);

// Create an index on the shard key field, shard and distribute equally
db.points.createIndex({x: 1})
// Enable sharding on the database
sh.enableSharding("db");
// shard and split
sh.shardCollection('db.points', {x: 1})
sh.splitAt('db.points', {x: 0});
sh.moveChunk('db.points', {x: 10}, "shard02");

// Create a second index
db.points.createIndex({x: "text"});

// move chunk
sh.moveChunk("db.points", {x: -10}, "shard02");

sh.status();

// drop index
db.points.dropIndex("x_text");
//
db.runCommand(
    {validateDBMetadata: 1, apiParameters: {version: "1", strict: true, deprecationErrors: true}});
