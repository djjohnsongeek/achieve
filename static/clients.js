//validate functions
function validate(form)
{
    var valid =  true;
    for (i = 0; i <form.length; i++)
    {
        if (!form[i].value)
        {   
            valid = false;
            form[i].style.border = "1px solid red";
        }

        else
        {
            form[i].style.border = "1px solid grey";
        }
    }
    return valid;
}

function validate_one(form)
{
    valid = false
    for (j = 0; j < form.length; j ++)
    {
        if (!form[j] || !form[j].value)
        {
            document.getElementById("div_teacher_team").style.border = "1px solid red";
        }

        else
        {
            valid = true
        }

        if (j == form.length - 1)
        {
            if (valid == true)
            {
                document.getElementById("div_teacher_team").style.border = "none";
                return true
            }
            else
            {
                return false
            }
        }
    }
}

//Listen for the add client button being clicked
document.getElementById("btn_add_client").addEventListener("click", function(event){

    // store client first and last name in variable
    var client_name = document.getElementById("client_name");
    var hrsForm = [client_name, document.getElementById("client_hours_start"), document.getElementById("client_hours_end")]
    var teamForm = [document.getElementById("assign_teacher0"), document.getElementById("assign_teacher1"), document.getElementById("assign_teacher2"),
                     document.getElementById("assign_teacher3")]

//prevent form submission
    event.preventDefault();
    //send GET request with clientname
    $.get("/addclient?clientname=" + client_name.value, function(data){
        console.log(data);
        if (data == false)
        {
            if (validate(hrsForm) && validate_one(teamForm))
            {
                document.getElementById("form_add_client").submit();
            }
        }
        else
        {
            alert("This Client already exists in the database");
        }
    });
});

//Listen for the remove client button being clicked
document.getElementById("btn_remove_client").addEventListener("click", function(event){

    //prevent form submission
    event.preventDefault();
    var client_name = document.getElementById("slct_client");
    
    if (!client_name.value)
    {
        client_name.style.border = "1px solid red";
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_remove_client").submit()
    }
});

//Listen for update client info button being clicked
document.getElementById("btn_update_client").addEventListener("click", function(event){
    //prevent form submission
    event.preventDefault();
    var client_name = document.getElementById("slct_update_client");

    if (!client_name.value)
    {
        client_name.style.border = "1px solid red";
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_update_client").submit();
    }

});