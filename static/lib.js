//validate functions

export function reveal_error(button, original_text)
{
    button.style.backgroundColor = "";
    button.innerText = original_text;
}

export function validate(form)
{
    var valid = true;
    for (var i = 0; i <form.length; i++)
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

export function validate_teachers(form)
{
    var lable = document.getElementById("teachers_title");
    var button = document.getElementById("btn_add_client");
    var valid = false;
    for (var j = 0; j < form.length; j ++)
    {
        if (!form[j] || !form[j].value)
        {
            continue;
        }

        else
        {
            valid = true
        }
    }

    if (valid == true)
    {
        lable.innerHTML = "Assign Teachers to Team";
        lable.style.color = "#212962";
        return true
    }
    else
    {
        lable.innerHTML = "Please select at least one Teacher";
        lable.style.color = "red";
        setTimeout(reveal_error, 3000);
        return false
    }
}