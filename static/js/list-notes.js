document.addEventListener('DOMContentLoaded', () => {
    // const tabs = document.getElementsByClassName("tab")
    // const myNotesTab = document.getElementById("my-notes-tab");
    // const sharedTab = document.getElementById("shared-tab");
    const sortSelect = document.getElementById("sort-by")
    const topBar = document.querySelector(".top-bar")
    const listPage = document.getElementById("list-notes-page")
    const viewPage = document.getElementById("view-page")
    const editPage = document.getElementById("edit-page")
    
    
    
    
    

    // sortSelect.addEventListener('change', e => {
    //     console.log(e)
    //     console.log(sortSelect.value)
    // })    


    // deleteButton.addEventListener("click", () => {
    //     created = ""
    //     window.location.replace("delete_note/"+created);
    // })

})

// window.onload = ()=>{    

// }

function view_note(subject, content, modified, created) {
    hide_list_notes_page()
    display_view_page()
}




// function newNote(){
//     console.log("trying to submit form...")
//     // hide_list_notes_page()
//     // display_edit_page()

//      // Create a form dynamically
//      var form = document.createElement("form");
//      form.setAttribute("method", "POST");
//      form.setAttribute("action", "edit_note_page");
//     //  document.appendChild(form)
//     // Create an input element for Full Name
//     // var FN = document.createElement("input");
//     // FN.setAttribute("type", "hidden");
//     // FN.setAttribute("name", "FullName");
//     // FN.setAttribute("placeholder", "Full Name");
//      // create a submit button
//      var s = document.createElement("input");
//      s.setAttribute("type", "submit");
//      s.setAttribute("value", "Submit");
//     // form.submit()
//     s.click()
//     console.log("tried to submit form...")
// }


function removeElement(element) {
    element.style.display = "none"
}

function showElement(element) {
    element.style.display = "block"
}


function hide_list_notes_page() {
    listPage.style.display = "none"
}

function display_edit_page() {
    editPage.style.display = "flex"
}

function display_view_page() {
    viewPage.style.display = "flex"
    viewPage.querySelector("#subject").innerHtml = subject
    viewPage.querySelector("#note-content").innerHtml = content
    viewPage.querySelector("#date-modified").innerHtml = content
    viewPage.querySelector("#date-created").innerHtml = content
}




// /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// for login, signup and forgot password page navigation...

// initially show login page

// problem: login page will be shown on refresh

// click on x button
// display none of current page
// show x page

