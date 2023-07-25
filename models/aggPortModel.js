var mongoose = require('mongoose');
var schema = mongoose.Schema;
var aggPortSchema = new schema({
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

var AggPort = mongoose.model('aggressive_portfolio',aggPortSchema)

module.exports=AggPort;