var mongoose = require('mongoose');
var schema = mongoose.Schema;
var safePortSchema = new schema({
    Move:{
        type: String,
        required: true
    },
    Stock_Price:{
        type:Number,
        required:true
    },
    Option_Premium:{
        type:Number,
        required:true
    },
    Expiration:{
        type: String,
        required:true
    },
    Ticker:{
        type: String,
        required:true
    },
    Buy_Number:{
        type:Number,
        required:true
    }
});

var SafePort = mongoose.model('safe_portfolio',safePortSchema)

module.exports=SafePort;