import {validate, validate_teachers, button_error} from "./lib.js"

//Listen for the add client button being clicked
document.getElementById("btn_add_client").addEventListener("click", function(event){

    // store client first and last name in variable
    var client_name = document.getElementById("client_name");
    var hrsForm = [client_name, document.getElementById("client_hours_start"), document.getElementById("client_hours_end")];
    var teamForm = document.getElementsByClassName("teachers");
    var button = document.getElementById("btn_add_client");
    var lable = document.getElementById("teachers_title");

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
            if (validate(hrsForm) && validate_teachers(teamForm, lable))
            {
                document.getElementById("form_add_client").submit();
            }

            else
            {
                // style button temporarely
                button_error(button);
            }
        }
        else
        {
            // style lable and text box
            document.getElementById("client_name_title").innerHTML = "Client Already Exists";
            document.getElementById("client_name_title").style.color = "red";
            client_name.style.border = "1px solid red";

            // style button temporarely
            button_error(button)
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
        button_error(button);
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_remove_client").submit()
    }
});