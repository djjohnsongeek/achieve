import {validate, validate_teachers, reveal_error} from "./lib.js"

//Listen for the add client button being clicked
document.getElementById("btn_add_client").addEventListener("click", function(event){

    // store client first and last name in variable
    var client_name = document.getElementById("client_name");
    var hrsForm = [client_name, document.getElementById("client_hours_start"), document.getElementById("client_hours_end")];
    var teamForm = document.getElementsByClassName("teachers");
    var button = document.getElementById("btn_add_client");

    // reset default look
    document.getElementById("client_name_title").innerHTML = "Add Client";
    document.getElementById("client_name_title").style.color = "#212962";
    client_name.style.border = "1px solid grey";

//prevent form submission
    event.preventDefault();
    //send GET request with clientname
    $.get("/addclient?clientname=" + client_name.value, function(data){
        if (data == false)
        {
            if (validate(hrsForm) && validate_teachers(teamForm))
            {
                document.getElementById("form_add_client").submit();
            }

            else
            {
                // style button temporarely
                var original_text = button.innerText;
                button.style.backgroundColor = "red";
                button.innerText = "Check for Errors";
                setTimeout(reveal_error, 3000, button, original_text);
            }
        }
        else
        {
            // style lable and text box
            document.getElementById("client_name_title").innerHTML = "Client Already Exists";
            document.getElementById("client_name_title").style.color = "red";
            client_name.style.border = "1px solid red";
            // style button temporarely
            var original_text = button.innerText;
            button.style.backgroundColor = "red";
            button.innerText = "Check for Errors";
            setTimeout(reveal_error, 3000, button, original_text);
        }
    });
});

//Listen for the remove client button being clicked
document.getElementById("btn_remove_client").addEventListener("click", function(event){
    var button = document.getElementById("btn_remove_client");
    //prevent form submission
    event.preventDefault();
    var client_name = document.getElementById("slct_client");
    
    if (!client_name.value)
    {
        client_name.style.border = "1px solid red";
        var original_text = button.innerText;
        button.innerText = "Check for Errors";
        button.style.backgroundColor = "red";
        setTimeout(reveal_error, 1500, button, original_text);
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_remove_client").submit()
    }
});