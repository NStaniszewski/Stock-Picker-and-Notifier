var express = require('express');
var router = express.Router();

/* GET users listing. */
router.get('/', function(req, res, next) {
    res.render('safe', { title: 'Stock Picker and Notifier' });
});

module.exports = router;
