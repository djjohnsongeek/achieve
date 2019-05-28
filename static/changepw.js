document.getElementById("btn_changepw").addEventListener("click", function(event){
    event.preventDefault();

    new_pw = document.getElementById("password_new");
    check_pw = document.getElementById("password_check");

    if (new_pw.value && check_pw.value)
    {
        if (new_pw.value === check_pw.value)
        {
            document.getElementById("form_change_pw").submit();
        }
        else
        {
            //alert("Passwords do not match")
            document.getElementById("change_pw_info").style.display = "block"
        }
    }

    if(!new_pw.value)
    {
        new_pw.style.border = "1px solid red";
    }

    if(!check_pw.value)
    {
        check_pw.style.border = "1px solid red";
    }
})