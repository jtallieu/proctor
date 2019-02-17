$(document).ready(function(){

    // Expand/collapse a single condition
    $('.proctor').on('click', '.condition-list .title', function(evt){
        // expand when the spans in the title are clicked
        if (!$(evt.target).is('button, input')) {
            $(this).closest('.condition').find('.body').toggle();
        }
    })

    // Expand/collapse all the condition bodies
    $('.selection.panel').on('click', '.header button#expand-all', function(evt){
        // expand all bodies
        $(this).closest('.header').next().find('.body').toggle(400);
    })

    var running_checks = false;
    var cancel_checks = false;

    // Run all enabled conditions for the context
    $('.selection.panel').on('click', 'button#check-selected', function(evt){
        var last_response_len = false;
        var this_button = $(evt.target);
        cancel_checks = false;
        // Button can work as a cancel button
        if (running_checks) {
            cancel_checks = true;
            this_button.prop("disabled", true);
            this_button.text("CANCELLING....");
            return;
        }

        // Collect the selected Proctor Id's
        var pids = $(this).closest('.selection.panel')
            .find('input[type="checkbox"]:checked')
            .map(function(){
                return $(this).closest('.condition').attr("id");
            }).get();
        
        // Clear out all the previous runs
        $('.results .result-list').empty();

        if (!pids.length) {
            alert("Nothing to run - select a few conditions");
        } else {
            // Check all the ones

            // Change the button to indicate Working
            // $(evt.target).prop("disabled", true);
            this_button.text("Stop Running Checks");
            this_button.addClass("cancel");

            // TODO: Cancel long runer
            // Make the request to check the selected ID's
            fetch("/proctor/" + window.context_class + "/check_all", {
                method: 'POST',
                body: JSON.stringify({pids: pids}),
                credentials: 'include',
                headers: { 
                    Accept : "application/fragment",
                    "Content-Type": "application/fragment"
                },
            }).then(function(response){
                var decoder = new TextDecoder();
                var reader = response.body.getReader();
                var current = '';
                var block_re = /\+{3}([\s\S]*?)---/g;
                var unmatched_index = 0;
                var passed = 0, detected = 0;
                
                running_checks = true;

                // Handle the errors
                if (response.status != 200) {
                    this_button.removeClass("cancel");
                    this_button.prop("disabled", false);
                    this_button.text("RUN PROCTOR");
                    return reader.read().then(function(result){
                        var message = decoder.decode(result.value || new Uint8Array, {stream: !result.done});
                        alert("Error: " + message);
                        return
                    }) 
                }


                function collect(){
                    return reader.read().then(function(result){
                        // Process the stream and pluck out frags from the stream
                        
                        var passed_nodes = [], detected_nodes = [];

                        current += decoder.decode(result.value || new Uint8Array, {stream: !result.done});
                        while ((ma = block_re.exec(current)) != null) {
                            unmatched_index = ma.index + ma[1].length;
                            var node = $($.parseHTML(ma[1]));

                            if (node.find('.detected-True').length) {
                                detected_nodes.push(node);
                                
                            } else {
                                passed_nodes.push(node);    
                            }
                        }

                        // Now insert them all in
                        if (detected_nodes.length) {
                            $('.results.detected .result-list').append(detected_nodes);
                            detected = $.find('.results.detected .context').length;
                            $('.results.detected > .header').html("Detected Conditions (" + detected + ")");
                        }
                        if(passed_nodes.length) {
                            $('.results.passed .result-list').append(passed_nodes);
                            passed = $.find('.results.passed .context').length;
                            $('.results.passed > .header').html("Passed Conditions (" + passed + ")");
                        }
                        current = current.slice(unmatched_index);

                        // Update the counts
                        
                        if (result.done || cancel_checks) {
                            reader.cancel("Done");
                            return {passed: passed, detected: detected};
                        }
                        else {
                            return collect();
                        }
                    })
                }
                return collect();
            }).then(function(stats) {
                // Collector should return stats, if not remain silent.
                if (stats) {
                    running_checks = false;
                    // Change the button to indicate Working
                    this_button.removeClass("cancel");
                    this_button.prop("disabled", false);
                    this_button.text("RUN PROCTOR");
                    alert("Passed " + stats.passed + " Failed " + stats.detected);
                }
            }).catch(function(error) {
                running_checks = false;
                this_button.removeClass("cancel");
                this_button.prop("disabled", false);
                this_button.text("RUN PROCTOR");
                alert("Something went wrong");
            });
        }
    })

})