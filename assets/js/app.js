var bb = {
  init: function(context){
    var self = this;
    self.context = context || {};
    self.Squares = Backbone.Collection.extend({
      initialize: function (models, options) {
        this.bind("add", options.view.addSquare);
      },
    }); 
    self.AppView = Backbone.View.extend({
      //el: $("body");
      initialize: function () {
        this.el = $("body");
        this.Squares = new self.Squares(null, {
          view: this
        });
        
        context.Squares = this.Squares;
        var options = {
          "dataSource":{
            page: 1,
            url:self.context.feedUrl,
          },
          collection:this.Squares
        };
        
        self.feedHandler.init(options);
      },
      /*events: {
        "click #feed": "getSquare",
        "click #next": "getSquare",
      },*/
      getSquare: function (event) {
        // $(event.target) will give us the event object.
        //alert($(event.target));
        self.feedHandler.getFeed();
      },
      nextSquare: function() {
        self.feedHandler.nextFeed();
      },
      addSquare: function (model) {
        if(model.attributes.content_type == 'tweet') {
          var sq = ich.tweet(model.attributes);
        }
        else if(model.attributes.content_type == 'text'){
          var sq = ich.text(model.attributes);
        } 
        else {
          var sq = ich.image(model.attributes);
        }
        $('.sqwag-list').append(sq);
      }
    });
    self.feedHandler = {
      init: function(context){
        var me = this;
        me.config = {
          "dataSource":{
            page: 1,
            url:"/api/publicsqwagfeed/",
          },
          "collection":null
        };
        $.extend(me.config,context)
      },
      getFeed : function(){
        var me = this;
        $.ajax({
          url: me.config.dataSource.url + me.config.dataSource.page,
          dataType: "json",
          success: function (data, textStatus, jqXHR) {
            if (data.status == 1) {
              me.config.dataSource.page = me.config.dataSource.page + 1;
              result = data.result;
              if (result.constructor == Array) {
                $.each(result, function (index, value) {
                  me.config.collection.add(value);
                });
              }
            }
            else {
              SQ.notify(data.error);
            }
          },
          complete: function(jqXHR, textStatus){
            smartDate.refresh();
          }
        }); 
      },
    };
    new self.AppView;
  }
};