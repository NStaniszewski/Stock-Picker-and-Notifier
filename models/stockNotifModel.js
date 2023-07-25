var mongoose = require('mongoose');
var schema = mongoose.Schema;
var stockNotifSchema = new schema({
    Move:{
        type: String,
        required: true
    },
    Ticker:{
        type:String,
        required:true
    },
    Price:{
        type:String,
        required:true
    },
    Reason:{
        type:String,
        required:true
    }
});

var StockNotifInd = mongoose.model('notif_stock_indicator',stockNotifSchema)

module.exports=StockNotifInd;