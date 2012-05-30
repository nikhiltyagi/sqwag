/*
    author: vaibhav saini
    twitter: saini_vaibhav
*/

var smartDate = {
    init: function(options) {
        var self = this;

        self.config = {
            "serverTime": "",
        };
        // merging two objects.
        if (null != options && options.constructor == Object) {
            $.extend(self.config, options);
        }
        self.min = 60;
        self.hour = self.min * 60;
        self.day = self.hour * 24;
        self.week = self.day * 7;
        self.month = 30 * self.day;
        self.year = 365 * self.day;
    },
    
    getSmartDate: function(serverTime) {
        var self = this;
        serverTime = serverTime || self.config.serverTime;
        var currentTime = Math.round(new Date().getTime() / 1000.0);
        var difference = currentTime - serverTime;
        var result = {
            "number" : 1,
            "prefix" : "about a",
            "unit" : "min",
            "suffix" : "ago."
        };
        var options = {};
        var number = "";
        var justNow = false;
        if (difference < self.min) {
            justNow = true;
        } else if (difference < self.hour) {
            var number = difference / self.min;
            options = {
                "unit" : "min",
            };
        } else if (difference < self.day) {
            var number = difference / self.hour;
            options = {
                "prefix": "about an",
                "unit" : "hour"                
            };
        } else if (difference < self.week) {
            var number = difference / self.day;
            options = {
                "unit" : "day"
            };
        } else if (difference < self.month) {
            var number = difference / self.week;
            options = {
                "unit" : "week"
            };
        } else if (difference < self.year) {
            var number = difference / self.month;
            options = {
                "unit" : "month"
            };
        } else {
            var number = difference / self.year;
            options = {
                "unit" : "year"
            };
        }
        if(justNow){
            return "just now";
        }else{
            number = Math.floor(number);
            options.number = number;
            $.extend(result, options);
            var returnString = "";
            if(number >1){
                result.unit = result.unit+"s";
                returnString = result.number+" "+ result.unit+" "+ result.suffix;
            }else{
                returnString = result.prefix+" "+ result.unit+" " + result.suffix;
            }
            return returnString;
        }
    },
    refresh: function(){
        var self = this;
        $(".pub-time").each(function(){
            if($(this).attr('data-time')){
                var serverTime = $(this).attr('data-time');
                $(this).text(self.getSmartDate(serverTime));
            }
        });
    }
};
smartDate.init();

/**
usage : 
    var options = {
        "serverTime": 1338397533  // in seconds. 
    };
    smartDate.init(options);
    alert(smartDate.getSmartDate());​
*/
