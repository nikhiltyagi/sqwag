(function ($) {
  Square = Backbone.Model.extend({
    //Create a model to hold friend atribute
    content_data: null,
    content_src: null,
    content_description:null,
    content_type:null
  });
  
  Squares = Backbone.Collection.extend({
    //This is our Friends collection and holds our Friend models
    initialize: function (models, options) {
      this.bind("add", options.view.addSquare);
      //Listen for new additions to the collection and call a view function if so
    }
  });
  
  AppView = Backbone.View.extend({
    el: $("body"),
    initialize: function () {
      this.Squares = new Squares( null, { view: this });
      //Create a friends collection when the view is initialized.
      //Pass it a reference to this view to create a connection between the two
    },
    events: {
      "click #add-friend":  "getSquare"
    },
    getSquare: function () {
        var self =this;
    	$.ajax({
    		url :"http://localhost:8000/api/user/homefeeds/",
    		dataType: "json",
    		success : function(data, textStatus, jqXHR){
    		    if(data.status==1){
    		        result = data.result;
    		        if(result.constructor==Array){
        		        $.each(result, function(index, value) { 
                          //alert(index + ': ' + value); 
                          console.log(index + ': '+ value.date_created);
                          self.Squares.add(value);
                        });
        		        /*$.each(result, funtion(index, value){
        		            console.log(value.date_created);
        		            self.Squares.add(value);
        		        });*/
        		    }
    		    }
    		        
    		}
    	});
      //var friend_name = prompt("Who is your friend?");
      //var friend_model = new Friend({ name: friend_name });
      //Add a new friend model to our friend collection
      //this.friends.add( friend_model);
    },
    addSquare: function (model) {
      //The parameter passed is a reference to the model that was added
      //$("#friends-list").append("<li>" + model.get('content_data') + "</li>");
      var sq = ich.sqwag(model.attributes);
      console.log(sq);
      $('.sqwag-list').append(sq);
      //Use .get to receive attributes of the model
    }
  });
  
  var appview = new AppView;
})(jQuery);
