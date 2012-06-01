var router = {
	init: function(context){
		var self = this;
		self.currentRoute;
		self.routes = {
			"settings":{"template":{"url":"/assets/templates/settings.html","elementId":"#content"}},
			"home" :  {"template":{"url":"/assets/templates/feed.html","elementId":"#content"},
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"feed" :  {"template":{"url":"/assets/templates/feed.html","elementId":"#content"},
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"myfeed" :  {"template":{"url":"/assets/templates/feed.html","elementId":"#content"},
				"bb_config":{
					"feedUrl":"/api/user/feeds/"
				}
			},
			"publicfeed" :  {"template":{"url":"/assets/templates/feed.html","elementId":"#content"},
				"bb_config":{
					"feedUrl":"/api/publicsqwagfeed/"
				}
			},
			"topsqwags" :  {"template":{"url":"/assets/templates/feed.html","elementId":"#content"},
				"bb_config":{
					"feedUrl":"/api/user/topsqwagsfeeds/"
				}
			},
			"logout" : {},
			"xyz" : {}
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
		$(template.elementId).load(template.url);
	}
}