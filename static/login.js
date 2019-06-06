document.getElementById("btn_login").addEventListener("click", function(event){
    event.preventDefault();
    username = document.getElementById("username")
    password = document.getElementById("password")

    if (username.value && password.value)
        document.getElementById("form-login").submit();

    if (!username.value)
    {
       username.style.border = "1px solid red";
    }
    if (!password.value)
    {
        password.style.border = "1px solid red";
    }
})