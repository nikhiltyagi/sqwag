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
    if(context.route){
      self.router.routeTo(context.route);
    }
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
  errorHandler: function(data){
    var error_string = "";
    if(data.error.constructor== Object){
      for (var key in data.error) {
        var obj = data.error[key];
        for (var prop in obj) {
          error_string = obj[prop]+" ";
        }
      }
    }else{
      error_string = data.error;
    }
    return error_string;
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

     
     $("#create-text-form").validate({
        rules: {
            content_data:{
              required: true
            }
        },
        messages: {
            content_data: {
              required: "you can not post an empty sqwag"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url: window.location.href+'api/square/create/',
            dataType: 'json',
            success: function(data) {
              if(data.status == 1) {
                self.refresh();
              }
              else {
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
            }
          };
          $(form).ajaxSubmit(options);
          return false; 
        }
    });

    $("#create-image-form").validate({
      rules: {
          content_file:{
            required: true
          }
      },
      messages: {
          content_file: {
            required: "please select an image to upload"
          }
      },
      submitHandler: function(form) {
        // do other stuff for a valid form
        var options = {
          url: window.location.href+'api/imagesquare/create/',
          dataType: 'json',
          success: function(data) {
            if(data.status == 1) {
              self.refresh();
            }
            else {
              var error_string = SQ.errorHandler(data);
              self.notify(error_string);
            }
          }
        };
        $(form).ajaxSubmit(options);
        return false; 
      }
  });
     
/*
    $('#sqwag-image-form form').ajaxForm({
      success: function(data) {
        self.refresh();
      }
    });*/

    $("#login-form").validate({
        rules: {
            username:{
              required: true
            },
            password:{
              required: true
            }
        },
        messages: {
            username: {
              required: "Please specify username"
            },
            password: {
                required: "We need your password to verify your credentials"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url: window.location.href+'sqwag/login/',
            dataType: 'json',
            success: function(data) {
              if(data.status == 1) {
                self.refresh();
              }
              else {
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
            }
          };
          $(form).ajaxSubmit(options);
          return false; 
        }
    });

   /*  $('#login-form form').ajaxForm({
      
    }); */

    $("#register-step1").validate({
        rules: {
            fullname:{
              required: true,
              maxlength: 25
            },
            email: {
              required: true,
              email: true
            },
            password:{
              required:true
            }
        },
        messages: {
            fullname: {
              required: "Please specify your fullname name",
              maxlength: "fullname should be less than 25 characters"
            },
            email: {
                required: "We need your email address to contact you",
                email: "Your email address must be in the format of name@domain.com"
            },
            password:{
              required: "Please enter Password"
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
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
              //self.close();
            }
          };

          $(form).ajaxSubmit(options);
          return false; 
        }
    });

    // fb register step 2 form
    
    $("#fb-step2-form").validate({
        rules: {
            username:{
              required: true,
              maxlength: 25
            },
            password:{
              required:true
            },
            tos_cbok:{
              required:true
            },
            user_id:{
              required:true
            }
        },
        messages: {
            username: {
              required: "Please specify username",
              maxlength: "username should be less than 25 characters"
            },
            password:{
              required: "Please enter Password"
            },
            tos_cbok:{
              required:"please select the checkbox to agree with TOS"
            },
            user_id:{
              required:"Some error detected. please restart the registration process."
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url: window.location.href+'sqwag/selectusername/',
            type:'post',
            dataType: 'json',
            beforeSubmit: function(){
              //skip
            },
            success: function(data) {
              if(data.status == 1) {
                SQ.refresh();
              }
              else {
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
              //self.close();
            }
          };

          $(form).ajaxSubmit(options);
          return false; 
        }
    });
    
    $("#fpwd-step1-form").validate({
        rules: {
            email:{
              required: true,
              email: true
            }
        },
        messages: {
            email: {
              required: "Please specify email",
              email: "Please enter valid email"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url: window.location.href+'sqwag/forgotpwd/',
            type:'post',
            dataType: 'json',
            beforeSubmit: function(){
              //skip
            },
            success: function(data) {
              if(data.status == 1) {
                $("#fpwd-step1").fadeOut();
                launchWindow('#fpwd-step2');
              }
              else {
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
              //self.close();
            }
          };

          $(form).ajaxSubmit(options);
          return false; 
        }
    });
    

    // validate email on blur
    /*$("#email").bind('blur',function(){
      
      $.ajax({
        url:"/sqwag/testname/",
        datatype:"json",
        type:"POST",
        data:{
        },
        success:function(data,textStatus,jqXHR){
          alert(data.result);
          SQ.notify(data.result);
        },
        error: function(data){
          alert("error: "+ data);
        }
      });

    });*/
  
//register-form-step2
    $("#register-form-step2").validate({
        rules: {
            username:{
              required: true
            },
            tos_cbok:{
              required: true
            },
            user_id:{
              required: true
            }
        },
        messages: {
            username: {
              required: "Please select a username"
            },
            tos_cbok: {
                required: "please select the checkbox to agree with TOS."
            },
            user_id:{
              required: "please restart the registration, we detected some error"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
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
                  var error_string = SQ.errorHandler(data);
                  self.notify(error_string);
                }
                self.close();
              }
          };
          $(form).ajaxSubmit(options);
          return false; 
        }
    });

    $("#feedback-form").validate({
      rules: {
            feedback:{
              required: true
            }
        },
        messages: {
            feedback: {
              required: "you can not submit an empty feedback!"
            }
        },
        submitHandler: function(form) {
          // do other stuff for a valid form
          var options = {
            url:"/api/feedback",
            type: "POST",
            dataType: 'json',
            success: function(data) {
              if(data.status == 1) {
                $("#feedback").val("");
                $("#feedback").DefaultValue("Thanks for your feedback!");
              }
              else {
                var error_string = SQ.errorHandler(data);
                self.notify(error_string);
              }
              self.close();
            }
          };
          $(form).ajaxSubmit(options);
          return false; 
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
    
    /*$("#submit-feedback").bind('click',function(){
      
    });*/

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
            var error_string = SQ.errorHandler(data);
            self.notify(error_string);
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
            var error_string = SQ.errorHandler(data);
            self.notify(error_string);
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
            var error_string = SQ.errorHandler(data);
            self.notify(error_string);
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