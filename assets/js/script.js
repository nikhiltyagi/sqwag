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
        /* data is NULL don't know why - praveen
        if(data.status == 1) {
          self.refresh();
        }
        else {
          self.notify(data.error);
        }
        */
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
      var square_id = $(this).data('id');
      self.backbone.feedHandler.reSqwag({'square_id' : square_id});
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