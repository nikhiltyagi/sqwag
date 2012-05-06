context = context || {};
(function ($) {
  Square = Backbone.Model.extend({
    content_data: null,
    content_src: null,
    content_description: null,
    content_type: null
  });

  Squares = Backbone.Collection.extend({
    initialize: function (models, options) {
      this.bind("add", options.view.addSquare);
    },
    url : '/api/user/homefeeds/'
  });

  AppView = Backbone.View.extend({
    el: $("body"),
    initialize: function () {
      this.Squares = new Squares(null, {
        view: this
      });
      context.Squares = this.Squares;
    },
    events: {
      "click #add-friend": "getSquare"
    },
    getSquare: function () {
      var self = this;
      $.ajax({
        url: "http://localhost:8000/api/user/homefeeds/",
        dataType: "json",
        success: function (data, textStatus, jqXHR) {
          if (data.status == 1) {
            result = data.result;
            if (result.constructor == Array) {
              $.each(result, function (index, value) {
                console.log(index + ': ' + value.date_created);
                self.Squares.add(value);
              });
            }
          }
          else if (data.status == 404) {
            notify(data.error);
          }

        }
      });
    },
    addSquare: function (model) {
      var sq = ich.sqwag(model.attributes);
      console.log(sq);
      $('.sqwag-list').prepend(sq);
    }
  });

  var appview = new AppView;
  
})(jQuery);