var mongoose = require('mongoose');
var schema = mongoose.Schema;
var aggPickSchema = new schema({
    Move:{
        type: String,
        required: true
    }
});

var AggPick = mongoose.model('aggressive_pick',aggPickSchema)

module.exports=AggPick;