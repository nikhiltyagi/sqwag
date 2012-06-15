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
        if(model.attributes.square){
          if(model.attributes.square.content_type == 'tweet') {
            var sq = ich.tweet(model.attributes);
          }
          else if(model.attributes.square.content_type == 'text'){
            var sq = ich.text(model.attributes);
          } 
          else if(model.attributes.square.content_type == 'image'){
            var sq = ich.image(model.attributes);
          }
        }
        else {
          // decide which ich.template to call... how?
          if(SQ.router.currentRoute=='toppeople'){
            // we have object of a user
            // now check the type of user object
            if(model.attributes.user_accounts && model.attributes.user_accounts.constructor==Array 
              && model.attributes.user_accounts.length){
              // its a connected account user_object
              if(model.attributes.user_accounts[0].account=='twitter'){
              }
              else if(model.attributes.user_accounts[0].account=='facebook'){
              }
              else if(model.attributes.user_accounts[0].account=='insta'){
              }

            }else{
              // it's a sqwag user object
            }
            var sq = ich.text(model.attributes)
          }
          
        }
        
        if(model.attributes.isPrepend){
          $('.sqwag-list').prepend(sq);
        }else{
          $('.sqwag-list').append(sq);
        }
      }
    });
    self.feedHandler = {
      init: function(context){
        var me = this;
        me.isNext = true;
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
        if(me.isNext){
          $.ajax({
            url: me.config.dataSource.url + me.config.dataSource.page,
            dataType: "json",
            success: function (data, textStatus, jqXHR) {
              if (data.status == 1) {
                if(data.isNext==true){
                  me.isNext = true;
                  me.config.dataSource.page = me.config.dataSource.page + 1;
                }else{
                  me.isNext = false;
                }
                result = data.result;
                if (result.constructor == Array) {
                  $.each(result, function (index, value) {
                    me.config.collection.add(value); 
                  });
                }
              }
              else {
                SQ.notify(data.error);
                if(data.status == 404){
                  if(SQ.router.currentRoute == 'home' || SQ.router.currentRoute=='feed'){
                    // no feeds for this user, suggest him some user to follow. later we will refactor
                    SQ.router.routeTo('toppeople');
                  }
                }
              }
            },
            complete: function(jqXHR, textStatus){
              smartDate.refresh();
            }
          }); 
        }
      },
      reSqwag : function(dataObject){
        var me =this;
        $.ajax({
          url:"/api/square/share",
          dataType: "json",
          type: "POST",
          data: dataObject,
          success: function (data, textStatus, jqXHR){
            if(data.status == 1){
              SQ.notify('re-sqwaged successfully!');
              result =  data.result.square;
              result.isPrepend = true; // to prepend it to the list. default is append
              me.config.collection.add(result);
            }else{
              SQ.notify(data.error);
            }
          },
          complete: function(jqXHR, textStatus){
            smartDate.refresh();
          }
        });
      }
    };
    new self.AppView;
  }
};