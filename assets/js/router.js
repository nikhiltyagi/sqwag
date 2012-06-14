var router = {
	init: function(context){
		var self = this;
		self.currentRoute;
		self.feedTemplate = {
			"url":"/assets/templates/feed.html",
			"targetElement":"#content",
			"templateRoot":"#sqwag-list-id",
			"isLoaded":false,

			getData: function(){
				$(self.feedTemplate.targetElement).html('<div id="sqwag-list-id" class="sqwag-list row"></div>');
				var config = SQ.router.routes[router.currentRoute];
				SQ.backbone.init(config.bb_config);
				SQ.backbone.feedHandler.getFeed();
			}
		};
		self.settingsTemplate = {
			"url":"/assets/templates/settings.html",
			"targetElement":"#content",
			"isLoaded":true,

			getData : function(){
				$(self.settingsTemplate.targetElement).load(self.settingsTemplate.url);
			}
		};
		self.formTemplate = {
			"url":"/assets/templates/form.html",
			"targetElement":"#content",
			"isLoaded":true,

			getData : function(){
				$(self.formTemplate.targetElement).load(self.formTemplate.url);
			}
		};
		self.routes = {
			"settings":{"template":self.settingsTemplate},
			"home" :{"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"feed" : {"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"myfeed" :  {"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/feeds/"
				}
			},
			"publicfeed" :  {"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/publicsqwagfeed/"
				}
			},
			"topsqwags" :  {"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/topsqwagsfeeds/"
				}
			},
			"userprofile" :  {"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/feeds/"
				}
			},
			"logout" : {},
			"sqwag-form" : {"template":self.formTemplate}
		};
		// merging two objects.
		if(null!=context && context.constructor==Object){
			if(null !=context.routes && context.routes.constructor==Object){
				$.extend(self.routes,context.routes);
			}
		}
	},

	routeTo : function(route){
		var self = this;
		self.currentRoute = route;
		var config = self.routes[route];
		self.loadTemplate(config.template);
	},
	
	loadTemplate : function(template){
		var self = this;
		if(template.isLoaded){
			// template already loaded. 
			template.getData();
		}else{
			// load the template
			$(template.targetElement).load(template.url,function(){
				ich.grabTemplates();
				template.isLoaded=true;
				template.getData();
			});
		}
	}
}