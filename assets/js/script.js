var SQ = {
  init: function(context) {
    var self = this;
    self.context = context;
    self.backbone = context.backbone;
    self.bindLinks();  
    self.bindForms(); 
    self.bindButtons();
    self.bindSqwags();
    self.router = context.router;
    //initialize routers 
    self.router.init();
    // route to a template
    self.router.routeTo(context.route);
    setInterval(smartDate.refresh, 60*1000);
  },

  close: function() {
    $('.close').click();
  },
  
  notify: function(data) {
    $('#console').text(data).fadeIn('slow');
  },
  
  refresh: function() {
    window.location.reload();
  },
  
  bindLinks: function() {
    var self = this;
    $('.js-load').click(function() {
      var route = $(this).attr('href').replace('#','');
      self.router.routeTo(route);
      return false;
    });

    $('.js-link').click(function() {
      var link = $(this).attr('href');
      var jxhr = $.get(link).complete(function() {
        self.refresh();
      });
      return false;
    });
  },
  
  bindForms: function() {
     var self = this;

     $('.sqwag-form form').ajaxForm({
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          /*result =  data.result;
          result.isPrepend = true; // to prepend it to the list. default is append
          SQ.backbone.feedHandler.config.collection.add(result);*/
          self.refresh();
        }
        else {
          self.notify(data.error);
        }
        self.close();
      }
    });

    $('#sqwag-image-form form').ajaxForm({
      success: function(data) {
        self.refresh();
      }
    });

     $('#login-form form').ajaxForm({
      url: window.location.href+'sqwag/login/',
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          self.refresh();
        }
        else {
          self.notify(data.error);
          self.close(); // TODO : refactor
        }
      }
    }); 
    
    $('#register-form form').ajaxForm({
      url: window.location.href+'sqwag/register/',
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          self.notify(data.status);
        }
        else {
          self.notify(data.error);
        }
        self.close();
      }
    });
  },
  bindButtons: function() {
    var self = this;
    $('.resqwag').live('click', function() {
      var user_square_id = $(this).data('id');
      self.backbone.feedHandler.reSqwag({'square_id' : user_square_id});
    });

    $(".action-retweet").live('click',function(){
      var user_square_id = $(this).data('id');
      self.backbone.feedHandler.reTweet({'square_id' : user_square_id});

    });

    $(".action-reply").live('click',function(){  // this needs a form. TODO for praveen :)
      var user_square_id = $(this).data('id');
      self.backbone.feedHandler.replyTweet(
        {
          'square_id' : user_square_id,
          'message': 'test',
          'user_handle' : 'saini_vaibhav'
        });
    });

    $(".action-favourite").live('click',function(){
      var user_square_id = $(this).data('id');
      self.backbone.feedHandler.favTweet({'square_id' : user_square_id});
    });
    
    $("#submit-feedback").bind('click',function(){
      $.ajax({
        url:"/api/feedback",
        dataType: "json",
        type: "POST",
        data: {
          'feedback': $("#feedback").val()
        },
        success: function (data, textStatus, jqXHR){
          if(data.status == 1){
            $("#resp-feedback").html("Thanks for you feedback :)");
          }else{
            SQ.notify(data.error);
          }
        },
        complete: function(jqXHR, textStatus){
          smartDate.refresh();
        }
      });
    });

    $(".sqwag-me").live('click',function(){
      $.ajax({
        url:"/api/followuser/",
        datatype:"json",
        type:"POST",
        data:{
          "producer":$(this).data('id')
        },
        success:function(data,textStatus,jqXHR){
          if(data.status==1){
            SQ.notify("success");
          }else{
            SQ.notify(data.error);
          }
        }
      });
    });

    $(".unsqwag").live('click',function(){
      var producer_id = $(this).data('id')
      $.ajax({
        url:"/api/unfollowuser/"+producer_id,
        datatype:"json",
        type:"GET",
        success:function(data,textStatus,jqXHR){
          if(data.status==1){
            SQ.notify("success");
          }else{
            SQ.notify(data.error);
          }
        }
      });
    });

    



    $(window).scroll(function () {
      if ($(window).height() + $(window).scrollTop() == $(document).height()) {
        self.backbone.feedHandler.getFeed();
      }
    });
  },
  
  bindSqwags: function() {
    $('.sqwag').live('mouseover mouseout', function(event) {
      var mask = $(this).find('.mask');
      if(event.type == 'mouseover') {
        mask.show();
      }
      else {
        mask.hide();
      }
    });
  },

  
}