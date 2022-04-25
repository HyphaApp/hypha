// This file is mimic of wagtail/client/src/components/StreamField/blocks/StreamBlock.js.
// Its purpose is to customize wagtail admin js(specially the ApplicationForms' form_fields part) as per the requirement

// https://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
function escapeHtml(unsafe)
{
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
 }

class BaseInsertionControl {
  // It picked up from wagtail/client/src/components/StreamField/blocks/BaseSequenceBlock.js
  constructor(placeholder, opts) {
    this.index = opts && opts.index;
    this.onRequestInsert = opts && opts.onRequestInsert;
  }

  setIndex(newIndex) {
    this.index = newIndex;
  }

  delete({ animate = false }) {
    if (animate) {
      $(this.element).slideUp().attr('aria-hidden', 'true');
    } else {
      $(this.element).hide().attr('aria-hidden', 'true');
    }
  }
}

class FormFieldStreamBlockMenu extends BaseInsertionControl{
  // Customizing the StreamBlockMenu
  constructor(placeholder, opts) {
    super(placeholder, opts);
    this.groupedChildBlockDefs = opts.groupedChildBlockDefs;
    const animate = opts.animate;

    const dom = $(`
      <div>
        <button data-streamblock-menu-open type="button" title="${escapeHtml(opts.strings.ADD,)}"
            class="c-sf-add-button c-sf-add-button--visible">
          <i aria-hidden="true">+</i>
        </button>
        <div data-streamblock-menu-outer>
          <div data-streamblock-menu-inner class="c-sf-add-panel"></div>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    this.element = dom.get(0);

    this.addButton = dom.find('[data-streamblock-menu-open]');
    this.addButton.click(() => {
      this.toggle();
    });

    this.outerContainer = dom.find('[data-streamblock-menu-outer]');
    this.innerContainer = dom.find('[data-streamblock-menu-inner]');
    this.hasRenderedMenu = false;
    this.isOpen = false;
    this.canAddBlock = true;
    this.disabledBlockTypes = new Set();
    this.close({ animate: false });
    if (animate) {
      dom.hide().slideDown();
    }
  }

  renderMenu() {
    if (this.hasRenderedMenu) return;
    this.hasRenderedMenu = true;

    this.groupedChildBlockDefs.forEach(([group, blockDefs]) => {
      if (group) {
        const heading = $('<h4 class="c-sf-add-panel__group-title"></h4>').text(
          group,
        );
        this.innerContainer.append(heading);
      }
      const grid = $('<div class="c-sf-add-panel__grid"></div>');
      this.innerContainer.append(grid);
      blockDefs.forEach((blockDef) => {
        if (escapeHtml(blockDef.name) != 'file') {
          const button = $(`
            <button type="button" class="c-sf-button action-add-block-${escapeHtml(blockDef.name,)}">
              <svg class="icon icon-${escapeHtml(blockDef.meta.icon,)} c-sf-button__icon" aria-hidden="true">
                <use href="#icon-${escapeHtml(blockDef.meta.icon)}"></use>
              </svg>
              ${escapeHtml(blockDef.meta.label)}
            </button>
          `);
          grid.append(button);
          button.click(() => {
            if (this.onRequestInsert) {
              this.onRequestInsert(this.index, { type: blockDef.name });
            }
            this.close({ animate: true });
          });
        }
      });
    });

    // Disable buttons for any disabled block types
    this.disabledBlockTypes.forEach((blockType) => {
      $(`button.action-add-block-${escapeHtml(blockType)}`, this.innerContainer).attr(
        'disabled',
        'true',
      );
    });
  }

  setNewBlockRestrictions(canAddBlock, disabledBlockTypes) {
    this.canAddBlock = canAddBlock;
    this.disabledBlockTypes = disabledBlockTypes;

    // Disable/enable menu open button
    if (this.canAddBlock) {
      this.addButton.removeAttr('disabled');
    } else {
      this.addButton.attr('disabled', 'true');
    }

    // Close menu if its open and we no longer can add blocks
    if (!canAddBlock && this.isOpen) {
      this.close({ animate: true });
    }

    // Disable/enable individual block type buttons
    $('button', this.innerContainer).removeAttr('disabled');
    disabledBlockTypes.forEach((blockType) => {
      $(`button.action-add-block-${escapeHtml(blockType)}`, this.innerContainer).attr(
        'disabled',
        'true',
      );
    });
  }

  toggle() {
    if (this.isOpen) {
      this.close({ animate: true });
    } else {
      this.open({ animate: true });
    }
  }
  open(opts) {
    if (!this.canAddBlock) {
      return;
    }

    this.renderMenu();
    if (opts && opts.animate) {
      this.outerContainer.slideDown();
    } else {
      this.outerContainer.show();
    }
    this.addButton.addClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'false');
    this.isOpen = true;
  }
  close(opts) {
    if (opts && opts.animate) {
      this.outerContainer.slideUp();
    } else {
      this.outerContainer.hide();
    }
    this.addButton.removeClass('c-sf-add-button--close');
    this.outerContainer.attr('aria-hidden', 'true');
    this.isOpen = false;
  }
}


class FormFieldStreamBlock extends window.wagtailStreamField.blocks.StreamBlock {
  // Overriding the StreamBlock

  _createInsertionControl(placeholder, opts) {
    // eslint-disable-next-line no-param-reassign
    opts.groupedChildBlockDefs = this.blockDef.groupedChildBlockDefs;
    return new FormFieldStreamBlockMenu(placeholder, opts);
  }

}


class FormFieldsBlockDefinition extends window.wagtailStreamField.blocks.StreamBlockDefinition {
  // Overriding the StreamBlockDefinition

  render(placeholder, prefix, initialState, initialError) {
    return new FormFieldStreamBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}

window.telepath.register('stream_forms.blocks.FormFieldsBlock', FormFieldsBlockDefinition);
