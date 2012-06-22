var router = {
	init: function(context){
		var self = this;
		self.currentRoute;
		self.feedTemplate = {
			"url":"/assets/templates/feed.html",
			"targetElement":"#content",
			"isLoaded":false,

			getData: function(){
				$("#main").html('<div id="content"></div>');
				$(self.feedTemplate.targetElement).html('<div id="sqwag-list-id" class="sqwag-list row"></div>');
				var config = SQ.router.routes[router.currentRoute];
				SQ.backbone.init(config.bb_config);
				SQ.backbone.feedHandler.getFeed();
			}
		};
		self.profileTemplate = {
			"url":"/assets/templates/profile.html",
			"targetElement":"#main",
			"isLoaded":false,

			getData: function(){
				$(self.profileTemplate.targetElement).load(self.profileTemplate.url, function() {
					// bind events

					this.bindEvents();

					function bindEvents(){

						$("#sub-msg-btn").bind('click',function(){
							$.ajax({
								url:"/api/uploadPersonalmsg/"+producer_id,
								datatype:"json",
								type:"POST",
								data:{
									'message':$("#personal-msg").val()
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

					};

					$(self.profileTemplate.targetElement).append('<div id="content"></div>');
					$('#content').html('<div id="sqwag-list-id" class="sqwag-list row"></div>');
					var config = SQ.router.routes[router.currentRoute];
					SQ.backbone.init(config.bb_config);
					SQ.backbone.feedHandler.getFeed();
				});				
			}
		};
		self.settingsTemplate = {
			"url":"/assets/templates/settings.html",
			"targetElement":"#content",
			"isLoaded":true,

			getData : function(){
				$(self.formTemplate.targetElement).load(self.settingsTemplate.url, function(){

					$("#twitter-connect").bind("click",function(){
						$.ajax({
				            url: "/sqwag/authtwitter",
				            dataType: "json",
				            success: function (data, textStatus, jqXHR) {
				              alert("received: "+data);
				            },
				            complete: function(jqXHR, textStatus){
				              smartDate.refresh();
				            },
				            error: function(jqXHR, textStatus, errorThrown){
				            	alert(textStatus+" : "+errorThrown);
				            }
			          	});
					})
				});
			}
		};
		self.topFeedTemplate = {
			"url":"/assets/templates/topfeeds.html",
			"targetElement":"#main",
			"isLoaded":false,

			getData: function(){
				$(self.topFeedTemplate.targetElement).load(self.topFeedTemplate.url, function() {
					// bind events

					this.bindEvents();

					function bindEvents(){

						$("#top-sqwag").bind('click',function(){
							$.ajax({
								url:"/api/uploadPersonalmsg/"+producer_id,
								datatype:"json",
								type:"POST",
								data:{
									'message':$("#personal-msg").val()
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

					};

					$(self.profileTemplate.targetElement).append('<div id="content"></div>');
					$('#content').html('<div id="sqwag-list-id" class="sqwag-list row"></div>');
					var config = SQ.router.routes[router.currentRoute];
					SQ.backbone.init(config.bb_config);
					SQ.backbone.feedHandler.getFeed();
				});				
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
			"settings":{
				"template":self.settingsTemplate},
			"home" :{
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"feed" : {
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/homefeeds/"
				}
			},
			"myfeed" :  {
				"template":self.profileTemplate,
				"bb_config":{
					"feedUrl":"/api/user/feeds/"
				}
			},
			"publicfeed" :  {
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/publicsqwagfeed/"
				}
			},
			"topsqwags" :  {
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/topsqwagsfeeds/"
				}
			},
			"userprofile" :  {
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/feeds/"
				}
			},
			"toppeople" : {
				"template":self.feedTemplate,
				"bb_config":{
					"feedUrl":"/api/user/topusersfeeds/"
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