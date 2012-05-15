context = context || {};
(function ($) {
  var Square = Backbone.Model.extend({
    content_data: null,
    content_src: null,
    content_description: null,
    content_type: null
  });

  var Squares = Backbone.Collection.extend({
    initialize: function (models, options) {
      this.bind("add", options.view.addSquare);
    },
    url : '/api/user/homefeeds/'
  });

  var AppView = Backbone.View.extend({
    el: $("body"),
    initialize: function () {
      this.Squares = new Squares(null, {
        view: this
      });
      context.Squares = this.Squares;
      ctx = {
        page:1,
        url:'/api/user/homefeeds/',
        collection:this.Squares
      };
      feedHandler.init(ctx);
    },
    events: {
      "click #feed": "getSquare",
      "click #next": "nextSquare"
    },
    getSquare: function (event) {
      // $(event.target) will give us the event object.
      //alert($(event.target));
      feedHandler.getFeed();
    },
    nextSquare: function() {
      feedHandler.nextFeed();
    },
    addSquare: function (model) {
      if(model.attributes.content_type == 'tweet') {
        var sq = ich.tweet(model.attributes);
      }
      else var sq = ich.text(model.attributes);
      console.log(sq);
      $('.sqwag-list').append(sq);
    }
  });

  var feedHandler = {
    init: function(context){

      var self = this;
      self.dataSource = {
        page : context.page,
        url : context.url
      };
      self.collection = context.collection;


    },
    getFeed : function(){
      var self = this;
      $.ajax({
        url: self.dataSource.url + self.dataSource.page,
        dataType: "json",
        success: function (data, textStatus, jqXHR) {
          if (data.status == 1) {
            result = data.result;
            if (result.constructor == Array) {
              $.each(result, function (index, value) {
                console.log(index + ': ' + value.date_created);
                self.collection.add(value);
              });
            }
          }
          else if (data.status == 404) {
            SQ.notify(data.error);
          }

        }
      }); 
    },
    nextFeed : function(){
      var self = this;
      self.dataSource.page = self.dataSource.page + 1;
      self.getFeed();
    }

  }

  var appview = new AppView;
})(jQuery);