Modernizr.load({
  load: [
  'js/libs/bootstrap-modal.min.js',
  'js/libs/underscore-min.js',
  'js/libs/backbone-min.js',
  'js/libs/ICanHaz.min.js'
  ],
  complete: function() {
    Modernizr.load({
      load: 'js/app.js',
      complete: function() {
        $("#add-friend").click();
      }
    });
  }
});