$(document).ready(function(){

    // Expand/collapse all the condition bodies
    $('.proctor').on('click', '.header button#expand-all', function(evt){
        // expand all bodies
        $(this).closest('.header').next().find('.body').toggle(400);
    })


    // Expand/collapse a single condition
    $('.proctor').on('click', '.condition-list .title', function(evt){
        // expand when the spans in the title are clicked
        if (!$(evt.target).is('button, input')) {
            $(this).closest('.condition').find('.body').toggle(400);
        }
    })

    // Run a single check
    $('.proctor').on('click', '.context .condition-list button[name="fix"]', function(evt){
        var condition = $(evt.target).closest('.condition');
        var condition_id = condition.attr('id');
        var ctxt_id = $(evt.target).closest('.context').attr('ctxt-id');
        var ctxt_class = $(evt.target).closest('.context').attr('ctxt-class');
        $(evt.target).prop("disabled", true);
        $(evt.target).text("FIXING ... ")
        $.ajax({
            url: "/proctor/fix/" + condition_id + "?model=" + ctxt_class + "&model_id=" + ctxt_id,
            headers: { 
                Accept : "application/fragment",
                "Content-Type": "application/fragment"
            },
            success: function(data) {
                condition.replaceWith($(data));
            },
            error: function(xhr, status, err) {
                $(evt.target).text("TIME OUT");
            }
        });
    })

    // Run a single check
    $('.proctor').on('click', '.context .condition-list button[name="check"]', function(evt){
        var condition = $(evt.target).closest('.condition');
        var condition_id = condition.attr('id');
        var ctxt_id = $(evt.target).closest('.context').attr('ctxt-id');
        var ctxt_class = $(evt.target).closest('.context').attr('ctxt-class');
        $(evt.target).prop("disabled", true);
        $(evt.target).text("CHECKING ... ")
        $.ajax({
            url: "/proctor/check/" + condition_id + "?model=" + ctxt_class + "&model_id=" + ctxt_id,
            headers: { 
                Accept : "application/fragment",
                "Content-Type": "application/fragment"
            },
            success: function(data) {
                el = $(data);
                condition.replaceWith(el);
                if (el.hasClass('detected-True')){
                    el.find('.body').toggle(400);
                }
            },
            error: function(xhr, status, err) {
                $(evt.target).prop("disabled", false);
                $(evt.target).text("ERROR: Try Again?")
            }
        });
    })

    // Run all enabled conditions for the context
    $('.proctor').on('click', '.context button#check-all', function(evt){
        // Check all the ones
        $(this).closest('.context').find('button[name="check"]:enabled').click();
    })

    // Run all checked conditions for the context
    $('.proctor').on('click', '.context button#check-selected', function(evt){
        // Check on the checked ones
        $(this).closest('.context').find('input[type="checkbox"]:checked').siblings('button[name="check"]').click()
    })

})