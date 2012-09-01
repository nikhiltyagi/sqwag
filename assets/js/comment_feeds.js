var cmtFeedHandler = {
  init: function(context){
    var me = this;
    me.isNext = true;
    me.config = {
      "dataSource":{
        page: 1,
        url:"api/restusersquare/",
      },
    };
    $.extend(me.config,context)
  },
  getFeed : function(){
    var me = this;
    if(me.isNext){
      $.ajax({
        url: me.config.dataSource.url + me.config.dataSource.user_square_id +'/'+ me.config.dataSource.page,
        dataType: "json",
        success: function (data, textStatus, jqXHR) {
          if (data.status == 1) {
            if(data.isNext==true){
              me.isNext = true;
              me.config.dataSource.page = me.config.dataSource.page + 1;
            }else{
              me.isNext = false;
            }
            result = data.result;
            if (result.constructor == Array) {
              $.each(result, function (index, value) {
                var sq = ich.comment(value);
                $("#feed_blk_cnt").append(sq);
              });
            }
          }
          else {
            SQ.notify(data.error);
          }
        },
        complete: function(jqXHR, textStatus){
          smartDate.refresh();
        }
      }); 
    }
  },
};