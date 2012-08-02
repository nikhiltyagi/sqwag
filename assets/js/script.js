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

    $("#register-step1").validate({
        rules: {
            fullname: "required",
            email: {
              required: true,
              email: true
            },
            password:{
              required:true
            }
        },
        messages: {
            fullname: "Please specify your fullname name",
            email: {
                required: "We need your email address to contact you",
                email: "Your email address must be in the format of name@domain.com"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url: window.location.href+'sqwag/register/',
            type:'post',
            dataType: 'json',
            beforeSubmit: function(){
              //skip
            },
            success: function(data) {
              if(data.status == 1) {
                $(".register_step1").hide();
                $(".register_step2").show();close
                $("#user_id").val(data.result);
                self.notify(data.result);
              }
              else {
                self.notify(data.error);
              }
              //self.close();
            }
          };

          $(form).ajaxSubmit(options);
          return false; 
        }
    });

/*
    $('#register-form form').ajaxForm({
      
    });*/

    $('#register-form-step2 form').ajaxForm({
      url: window.location.href+'sqwag/selectusername/',
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          $(".register_step2").hide();
          $(".register_step1").show();
          $("#user_id").val("");
          self.notify(data.result);
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
// open the popup and get usersquare
    $("").live('click',function(){
      // code to open the modal window/ fancybox
      // once the modal window opens. hit a ajax call to get userSquare info
      var usersquare_id = $(this).data('id')
      $.ajax({
        url:"/api/usersquare/"+usersquare_id,
        datatype:"json",
        type:"GET",
        success:function(data,textStatus,jqXHR){
          if(data.status==1){
            // populate data
            
          }else{
            SQ.notify(data.error);
          }
        }
      });
    });


    $(window).scroll(function () {
      if ($(window).height() + $(window).scrollTop() == $(document).height()) {
        if (self.router.currentRoute!='publicfeed' && self.router.currentRoute!='toppeople' ){
          self.backbone.feedHandler.getFeed();  
        }
      }
    });
  },
  
  bindSqwags: function() {
    $('.feed_blk').live('mouseover mouseout', function(event) {
      var mask = $(this).find('.align_right');
      if(event.type == 'mouseover') {
        mask.show();
      }
      else {
        mask.hide();
      }
    });
  },

  
}