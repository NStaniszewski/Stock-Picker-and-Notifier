var mongoose = require('mongoose');
var schema = mongoose.Schema;
var safePickSchema = new schema({
    Move:{
        type: String,
        required: true
    }
});

var SafePick = mongoose.model('safe_pick',safePickSchema)

module.exports=SafePick;