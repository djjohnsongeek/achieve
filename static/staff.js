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

// listen for add staff button
document.getElementById("btn_add_staff").addEventListener("click", function(event){
    event.preventDefault();
    var staff_name = document.getElementById("staff_name");
    var requiredFields = [staff_name, document.getElementById("staff_hours_start"), document.getElementById("staff_hours_end")]
    if (validate(requiredFields))
    {
        document.getElementById("form_add_staff").submit();
    }
    else
    {
        console.log("Form Not Submitted")
    }
});

document.getElementById("btn_remove_staff").addEventListener("click", function(event){
    event.preventDefault();
    var staff_name = document.getElementById("slct_staff_remove");

    if (!staff_name.value)
    {
        staff_name.style.border = "1px solid red";
    }
    else
    {
        document.getElementById("form_remove_staff").submit();
    }
})

document.getElementById("btn_update_staff").addEventListener("click", function(event){
    event.preventDefault();
    var staff_name = document.getElementById("slct_staff_update");

    if (!staff_name.value)
    {
        staff_name.style.border = "1px red solid";
    }
    else
    {
        staff_name.style.border = "1px grey solid";
        document.getElementById("form_update_staff").submit();
    }
});