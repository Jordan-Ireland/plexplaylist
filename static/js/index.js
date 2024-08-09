function allShowSearch() {
    // Declare variables
    var input, filter, select, options, a, i;
    input = document.getElementById('allShowSearch');
    filter = input.value.toUpperCase();
    select = document.getElementById("showList");
    options = $("#showList").find(".panel-title");

    // Loop through all list items, and hide those who don't match the search query
    $.each(options, function (index, element) { 
        a = $(element).text();
        if (a.toUpperCase().indexOf(filter) > -1) {
            $(element).show();
        } else {
            $(element).hide();
        }
    });
}

var changed = false;

function updatePlaylistButton() {
    $("#generatePlaylist").prop("disabled", !changed);
}

function addShow(element) {
    $("#loading").show();
    changed = true;
    id = $(element).data("value");

    $.ajax({
        accepts: "application/json",
        contentType: "application/json",
        url: "/getshowdata?showId=" + id,
        type: "GET",
    }).done(function (data) {
            addShowElementToList(data);

            updatePlaylistButton();
            $("#loading").hide();
    });
}

function addShowElementToList(data) {
    changed = true;
    var allShowsList, selectList, newOption;
    allShowsList = $("#showList");
    selectList = $("#selectedShowsPanel");
    for (var i = 0; i < data.length; i++) {
        newOption = createShowElement(data[i])
        newOption = $(selectList).append(newOption);            

        $(newOption).find(".showCheckbox").on("click", function (e) {
            e.stopPropagation();
            if($(this).data("season") != undefined) {
                var checked = $(this).prop("checked");
                $($(this).parent().attr("href")).find(".showCheckbox").each(function() {
                    changed = true;
                    $(this).prop("checked", checked);
                    updatePlaylistButton();
                });
            }
        });
        
        $(allShowsList).find(".available-show").each(function() {
            if($(this).data("value") == data[i].id) {
                $(this).hide();
            }
        })

        $(newOption).find(".remove-show").on("click", function() {
            removeShowFromList($(this).data("id"));
            updatePlaylistButton();
        });
    }
    
}

function removeShowFromList(showId) {
    changed = true;
    var allShowsList = $("#showList");

    $(allShowsList).find(".available-show").each(function() {
        if($(this).data("value") == showId) {
            // console.log($(this));
            $(this).show();
        }
    });

    $("#" + showId).remove();
}

function generatePlaylist() {
    $("#loading").show();
    changed = false;
    updatePlaylistButton();
    var selectedOptions = $("#selectedShows #selectedShowsPanel .panel");
    var selectedOptionValues = {"shows": []};
    $.each(selectedOptions, function (index, show) { 
        var showId = $(show).attr("id");
        selectedOptionValues["shows"].push({"id": showId, "seasons": []});

        var seasonsLi = $($(show).find(".panel-heading h4 a").attr("href") + ">ul>li");

         $.each(seasonsLi, function (sIndex, season) { 
            selectedOptionValues["shows"][index]["seasons"].push({"sIndex": $(season).find(".panel-heading").data("seasonid"),"checked": $(season).find("div>h4>a>input").prop("checked"), "episodes": []});
            var episodesLi = $($(season).find(".panel-heading h4 a").attr("href") + ">ul>li");

             $.each(episodesLi, function (eIndex, episode) { 
                selectedOptionValues["shows"][index]["seasons"][sIndex]["episodes"].push({"eIndex": $(episode).data("episodeid"), "checked": $(episode).find("input").prop("checked")});
             });
         });
    });
    // console.log(selectedOptionValues);

    var jsonData = JSON.stringify(selectedOptionValues);

    $.ajax({
        accepts: "application/json",
        contentType: "application/json",
        url: "/generateplaylist",
        data: jsonData,
        type: "POST",
    }).done(function (data) {        
        // console.log("Done generating playlist", data);
        $.ajax({
            accepts: "application/json",
            contentType: "application/json",
            url: "/getcurrentplaylist",
            type: "GET",
        }).done(function (data) {
            updatePlaylist(data);
            // console.log("Here's the results of playlist creation", data);
            $("#loading").hide();
        });
    });
}

function regeneratePlaylist() {    
    $("#loading").show();
    $.ajax({
        accepts: "application/json",
        contentType: "application/json",
        url: "/regenerateplaylist",
        type: "GET",
    }).done(function (data) {        
        updatePlaylist(data);
        $("#loading").hide();
        // console.log("Done regenerating playlist", data);
    });
}

function createShowElement(showOriginal) {
    var show = JSON.parse(JSON.stringify(showOriginal));
    var title = show.title.replace(/ /g, '');
    for (var i = 0; i < title.length; i++) {
        charInt = parseInt(title[i]);
        if (charInt == NaN)
            continue;
        title = title.replace(charInt, String.fromCharCode(charInt + 64));
    }
    title = title.replace(/[^a-zA-Z0-9]/g, '');

    for (var i = 0; i < show.seasons.length; i++) {
        for (var j = 0; j < show.seasons[i].episodes.length; j++) {
            show.seasons[i].episodes[j].title = show.seasons[i].episodes[j].title.replace(' ', '');
        }
    }

    var element = '<div id="' + show.id + '" class="panel panel-default">' +
                            '<div class="panel-heading" role="tab" id="' + title + show.year + 'Heading">' +
                                '<h4 class="panel-title">' +
                                    '<a class="collapsed show" data-toggle="collapse" href="#' + title + show.year + 'SEASONS" aria-expanded="false" aria-controls="' + title + show.year + 'SEASONS">' +
                                    showOriginal.title + ' (' + showOriginal.year + ')' + 
                                    '</a>' +
                                    '<button data-id="' + show.id + '" class="remove-show btn"><i style="color:red;" class="fa-solid fa-minus"></i></button>'+
                                '</h4>' +
                            '</div>' +

                    '<div id="' + title + show.year + 'SEASONS" class="panel-collapse collapse" role="tabpanel" aria-labelledby="' + title + show.year + 'Heading">' +
                        '<ul class="list-group indent-1">';
                        
        for (var i = 0; i < show.seasons.length; i++) {
            element += '<li>' +
                            '<div class="panel-heading" role="tab" data-seasonId="' + show.seasons[i].sIndex + '" id="' + title + show.year + 'SEASON' + (i+1) + 'Heading">' +
                                '<h4 class="panel-title">' +
                                    '<a class="collapsed" data-toggle="collapse" href="#' + title + show.year + 'SEASON' + (i+1) + 'EPISODES" aria-expanded="false" aria-controls="' + title + show.year + 'SEASON' + (i+1) + 'EPISODES">' +
                                        '<input ' + (show.seasons[i].checked ? "checked" : "") + ' data-season="' + (i+1) + '" class="showCheckbox" type="checkbox" /> ' + showOriginal.title + ' (' + showOriginal.year + ') ' + 'S' + (i+1) +
                                    '</a>' +
                                '</h4>' +
                            '</div>' +
                            '<div id="' + title + show.year + 'SEASON' + (i+1) + 'EPISODES" class="panel-collapse collapse" role="tabpanel" aria-labelledby="' + title + show.year + 'SEASON' + (i+1) + 'Heading">' +
                                '<ul class="list-group indent-1">';
            for (var j = 0; j < show.seasons[i].episodes.length; j++) {
                element += '<li data-episodeId="' + show.seasons[i].episodes[j]['eIndex'] + '" class="list-group-item"><input ' + (show.seasons[i].episodes[j].checked ? "checked" : "") + ' class="showCheckbox" type="checkbox" /> ' + showOriginal.title + ' (' + showOriginal.year + ') ' + 'S' + (i+1) +'E' + (j+1) + ' - ' + showOriginal.seasons[i].episodes[j].title + '</li>';
            }
            element += '</ul>' +
                    '</div>';
                            
            element += '</li>';
        }
                        
        element += '</ul>' +
            '</div>' +
        '</div>';

    return element;
}

function updatePlaylist(data) {     
    $("#loading").show();
    $("#playlistBody").html("");   
    for (var i = 0; i < data['playlist'].length; i++) {
        $("#playlistBody").append(addPlaylistElement(data['playlist'][i]));
    }
    $("#loading").hide();
}

function addPlaylistElement(show) {
    return '<tr>' +
                '<td>' + show[0] + '</td>' +
                '<td>' + show[2] + '</td>' +
                '<td>' + show[3] + '</td>' +
                '<td>' + show[1] + '</td>' +
            '</tr>';
}

$(document).ready(function () {
    $("#loading").show();
    $.ajax({
        accepts: "application/json",
        contentType: "application/json",
        url: "/getselectedshows",
        type: "GET",
    }).done(function (data) {
        addShowElementToList(data);
        // console.log(data);
    });

    $.ajax({
        accepts: "application/json",
        contentType: "application/json",
        url: "/getcurrentplaylist",
        type: "GET",
    }).done(function (data) {
        updatePlaylist(data);
        // console.log("Here's the results of current playlist", data);
    });

    $(".available-show").on("click", function () {
        changed = true;
        addShow(this);
    });

    changed = false;
    updatePlaylistButton();

    $(".showCheckbox").on("click", function (e) {
        changed = true;
        e.stopPropagation();
    });

    $("#loading").hide();
    // $(".option").on("click", function () {
    //     addShow(this);
    // });
});