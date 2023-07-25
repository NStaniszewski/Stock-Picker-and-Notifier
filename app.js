var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
var mongoose = require('mongoose');
var nodemailer=require('nodemailer');
var schedule=require('node-schedule');

var StockNotifInd = require('./models/stockNotifModel')
var Email = require('./models/emailModel');
var SafePick = require('./models/safePickModel');
var AggPick = require('./models/aggPickModel');
var SafePort = require('./models/safePortModel');
var AggPort = require('./models/aggPortModel');
var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var aggroRouter = require('./routes/aggressive');
var safeRouter = require('./routes/safe');
const { send, title } = require('process');

var app = express();

//mongodb stuff
var uri = 'mongodb+srv://';
mongoose.connect(uri,{useNewUrlParser:true,useUnifiedTopology:true})
  .then((result)=>console.log('Connected'),app.listen())
  .catch((err)=>console.log(err));

//nodemailer stuff
var transporter=nodemailer.createTransport({
  service:'gmail',
  auth:{
    user:'@gmail.com',
    pass:'token'
  }
});

var stock_email_notifications=schedule.scheduleJob('15 */24 * * *',()=>{
  var wait_start = ms => new Promise(res => setTimeout(res, ms));

  async function get_email_ary(){
    var email_array=[];
    Email.find()
    .then((result_email)=>{
      console.log('emails:'+result_email);
      for(var i=0;i<result_email.length;i++){
        email_array.push(result_email[i].email);
      }
    })
    .catch((err_email)=>{
      console.log('emails:'+err_email);
    }); 
    return email_array;
  }

  async function send_stock_notifs(){
    var email_ary=await get_email_ary();

    StockNotifInd.find()
    .then((result_stockind)=>{
        console.log('stock notif inds grabbed');
        for(var j=0;j<result_stockind.length;j++){
          email_ary.forEach((current_email)=>{
            console.log(current_email);
            var mailOptions={
              from:'@gmail.com',
              to: current_email,
              subject:result_stockind[j].Move+' '+result_stockind[j].Ticker,
              text:'Price: '+result_stockind[j].Price+'\n'+result_stockind[j].Reason
            };
            transporter.sendMail(mailOptions,function(err_sending,info){
              if (err_sending){
                console.log(err_sending);
              }else{
                console.log('email sent:'+info.response);
              }
            });
          })
            
        }
        console.log('done notifying');
      })
    .catch((err_notif)=>{
        console.log('stock notif inds:'+err_notif);
    });
  }
  async function delete_stock_inds(){
    await wait_start(10000); //delays the start time of the clear database method so sending the email with that databases info can run before deletion, 10000 = 10 seconds
    StockNotifInd.deleteMany({})
    .then(function(){
      console.log('empied notifier database');
    })
    .catch(function(err){
      console.log(err);
    });
  }

  send_stock_notifs();
  delete_stock_inds();
});

// view engine setup
app.use(express.static(path.join(__dirname,'views')));
//app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/emails',(req,res)=>{
  var email = new Email({
    email: req.body.emailInput
  });
  email.save()
    .then((result)=>{
      res.redirect('/emails')
    })
    .catch((err)=>{
      console.log(err);
    });
});

app.get('/emails/:id',(req,res)=>{
  var id=req.params.id
  Email.findById(id)
    .then(result=>{
      console.log(result);
    })
    .catch((err)=>{
      console.log(err);
    });
});

app.get('/emails',(req,res)=>{
  Email.find()
    .then((result)=>{
      console.log(result);
      res.redirect('/')
    })
    .catch((err)=>{
      console.log(err);
    });
});

app.delete('/emails/:id',(req,res)=>{
  var id=req.params.id;
  Email.findByIdAndDelete(id)
    .then((result)=>{
      res.json({redirect:'/emails'});
    })
    .catch((err)=>{
      console.log(err);
    });
});

app.get('/safe',function(req,res){
  var wait_start = ms => new Promise(res => setTimeout(res, ms));

  async function get_portfolio_ary(){
    var port_ary=[];
    var disp_string='';
    SafePort.find()
    .then((result)=>{
      //console.log(result);
      for(var i=0;i<result.length;i++){
        disp_string=result[i].Move + ' '+result[i].Ticker + ' @ ' + result[i].Stock_Price +' + Premium:'+result[i].Option_Premium+' Number: ' +result[i].Buy_Number+' Expires: '+result[i].Expiration;
        port_ary.push(disp_string); 
      }
      
    })
    .catch((err)=>{
      console.log(err);
      
    });
    return port_ary;
  }

  async function display_window(){
    var portfolio_ary= await get_portfolio_ary();
    await wait_start(10);

    SafePick.find()
    .then((result)=>{
      res.render('safe',{ title: 'Stock Picker and Notifier',picks:result,portfolio:portfolio_ary})
    })
    .catch((err)=>{
      console.log(err);
    });
  }
  display_window();
});

app.get('/aggressive',function(req,res){
  var wait_start = ms => new Promise(res => setTimeout(res, ms));

  async function get_portfolio_ary(){
    var port_ary=[];
    var disp_string='';
    AggPort.find()
    .then((result)=>{
      //console.log(result);
      for(var i=0;i<result.length;i++){
        disp_string=result[i].Move + ' '+result[i].Ticker + ' @ ' + result[i].Stock_Price +' + Premium:'+result[i].Option_Premium+' Number: ' +result[i].Buy_Number+' Expires: '+result[i].Expiration;
        port_ary.push(disp_string); 
      }
      
    })
    .catch((err)=>{
      console.log(err);
      
    });
    return port_ary;
  }

  async function display_window(){
    var portfolio_ary= await get_portfolio_ary();
    await wait_start(10);

    AggPick.find()
    .then((result)=>{
      res.render('aggressive',{ title: 'Stock Picker and Notifier',picks:result,portfolio:portfolio_ary})
    })
    .catch((err)=>{
      console.log(err);
    });
  }
  display_window();
});

app.use('/', indexRouter);
app.use('/users', usersRouter);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
