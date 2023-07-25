var express = require('express');
var router = express.Router();

/* GET users listing. */
router.get('/', function(req, res, next) {
    res.render('aggressive', { title: 'Stock Picker and Notifier' });
});

module.exports = router;
