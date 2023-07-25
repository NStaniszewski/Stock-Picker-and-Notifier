var mongoose = require('mongoose');
var schema = mongoose.Schema;
var emailSchema = new schema({
    email:{
        type: String,
        required: true,
        unique:true
    }
});

var Email = mongoose.model('email',emailSchema)

module.exports=Email;