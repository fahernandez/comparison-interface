function hintItem(clickedItem) {
  clickedItem1 = clickedItem.hasClass("left-item");
  clickedItem2 = clickedItem.hasClass("right-item");
  item1 = document.getElementById("left-item");
  item2 = document.getElementById("right-item");
  isItem1Selected = item1.classList.contains('selected-item');
  isItem2Selected = item2.classList.contains('selected-item');
  idItem1 = document.getElementById('item_1_id').value
  idItem2 = document.getElementById('item_2_id').value

  // Set the clicked item DOM object
  clickedItem = item1;
  if (clickedItem2) {
    clickedItem = item2;
  }

  // Case 1: No item was selected. Result: At least one item was selected
  if (!isItem1Selected && !isItem2Selected) {
    // Clean the all visual hints
    cleanVisualHint('selected-item', item1, item2);
    cleanVisualHint('selection-tied', item1, item2);
    
    // Show the item item as selected
    addVisualHint('selected-item', clickedItem, 'selected');

    // Activate the confirm button
    activateConfirmButton();

    // Set the selected item
    itemId = idItem1;
    if (clickedItem2) {
      itemId = idItem2;
    }
    setSelectedItem(itemId);

    return
  }

  // Case 2: Just one item was selected. Result: Tied case.
  if (
    (clickedItem1 && !isItem1Selected && isItem2Selected) ||
    (clickedItem2 && !isItem2Selected && isItem1Selected)
  ) {
      // Clean the selected-items class
      cleanVisualHint('selected-item', item1, item2);
      cleanVisualHint('selection-tied', item1, item2);

      // Show both items as selected (Tied case)
      addVisualHint('selection-tied', item1, 'tied');
      addVisualHint('selection-tied', item2, 'tied');

      // Activate the confirm button
      activateConfirmButton()

      // Clean the selected item value
      setSelectedItem("");

      return
  }

  // Case 3: One item was unselected. Result: The other item gets the bigger Label
  if (isItem1Selected && isItem2Selected) {
    // Clean the tied selection class
    cleanVisualHint('selected-item', item1, item2);
    cleanVisualHint('selection-tied', item1, item2);

    // Activate the confirm button
    activateConfirmButton()
    
    // Defined the selected and unselected items. The selected item will be
    // the item not clicked.
    selected = item1
    selected_component_id = 'item_1_id'
    if (clickedItem1) {
      selected = item2
      selected_component_id = 'item_2_id'
    } 

    // Mark as selected the not clicked item.
    addVisualHint('selected-item', selected, 'selected');

    // Set as selected id the value of the not clicked item.
    itemId = idItem2;
    if (clickedItem2) {
      itemId = idItem1;
    }
    setSelectedItem(itemId);

    return
  }

  // Case 4: The only selected item is unselected. Result: Confirm button is disabled
  if (
    (clickedItem2 && isItem2Selected && !isItem1Selected) ||
    (clickedItem1 && isItem1Selected && !isItem2Selected)
  ) {
    // Clean the selected-items class
    cleanVisualHint('selected-item', item1, item2);
    cleanVisualHint('selection-tied', item1, item2);

    // Deactive the confirm button
    deactivateConfirmButton()

    // Clean the seleted item id
    setSelectedItem("");

    return
  }
}

function cleanVisualHint(itemClass, item1, item2) {
  item1.classList.remove(itemClass);
  item2.classList.remove(itemClass);
  $(".centered").remove();
}

function addVisualHint(itemClass, item, type) {
  selectedItemIndicator = document.getElementById('selected_item_indicator').value
  tiedComparisonIndicator = document.getElementById('tied_items_indicator').value
  hintElement = '<div class="centered" style="pointer-events:none;"><h1 style="font-size:60px; color:green; font-weight: bold;pointer-events:none;">'+ selectedItemIndicator + '</h1></div>';
  if (type == "tied") {
    hintElement = '<div class="centered" style="pointer-events:none;"><h1 style="font-size:60px; color:blue; font-weight: bold;pointer-events:none;">'+ tiedComparisonIndicator + '</h1></div>';
  }

  item.classList.add(itemClass);
  element = document.createRange().createContextualFragment(hintElement);
  item.after(element);
}

function deactivateConfirmButton(){
  $("#confirm-button-m").prop('disabled', true);
  $("#confirm-button-m").addClass('disabled');
  $("#confirm-button-d").prop('disabled', true);
  $("#confirm-button-d").addClass('disabled');
}

function activateConfirmButton(){
  $("#confirm-button-m").prop('disabled', false);
  $("#confirm-button-m").removeClass('disabled');
  $("#confirm-button-d").prop('disabled', false);
  $("#confirm-button-d").removeClass('disabled');
}

function setSelectedItem(value) {
  document.getElementById("selected_item_id").value = value
}

$("img").click(function() {
	hintItem($(this));
});