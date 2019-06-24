import {validate_teachers, validate, button_error} from "./lib.js"

// listen for add-class form submission
document.getElementById("btn_add_class").addEventListener("click", function(event){
    //prevent submission
    event.preventDefault();

    // store form data
    var class_data = [document.getElementById("class_name"), document.getElementById("class_hours_start"), document.getElementById("class_hours_end")];
    var button = document.getElementById("btn_add_class");
    var teachers = [document.getElementById("class_teacher1"), document.getElementById("class_teacher2")];
    var subs = [document.getElementById("sub_teacher1"), document.getElementById("sub_teacher2"), document.getElementById("sub_teacher3"),
     document.getElementById("sub_teacher4")];
    var teacher_num = document.getElementById("class_rq");
    var lable1 = document.getElementById("lable_class_teachers");
    var lable2 = document.getElementById("lable_sub_teachers");

    // reset defualt look
    class_name.style.border = "";

    // validate forms
    if (!validate(class_data))
    {
        button_error(button)
    }

    else if (validate_teachers(teachers, lable1) && validate_teachers(subs, lable2))
    {
        if (teacher_num.value)
        {
            document.getElementById("form_add_class").submit();
        }
        else
        {
            teacher_num.style.border = "1px solid red";
            button_error(button)
        }
    }

    else
    {
        button_error(button)
    }
});

//listen for remove-class form submission

document.getElementById("btn_remove_class").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_remove_class");

    // validate form
    if(!document.getElementById("slct_class").value)
    {
        document.getElementById("slct_class").style.border = "1px solid red";
        button_error(button)
    }
    else
    {
        document.getElementById("form_remove_class").submit();
    }

});