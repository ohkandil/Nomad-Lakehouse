// Global type declarations for @opentui/react JSX components
import type { ExtendedIntrinsicElements } from '@opentui/react/src/types/components';
import type { baseComponents } from '@opentui/react/src/components/index';

// Augment the JSX namespace with OpenTUI components
declare global {
  namespace JSX {
    interface IntrinsicElements extends ExtendedIntrinsicElements<typeof baseComponents> {
      // These are the base component names from @opentui/react
      box: IntrinsicElements['box'];
      text: IntrinsicElements['text'];
      input: IntrinsicElements['input'];
      code: IntrinsicElements['code'];
      markdown: IntrinsicElements['markdown'];
      select: IntrinsicElements['select'];
      textarea: IntrinsicElements['textarea'];
      scrollbox: IntrinsicElements['scrollbox'];
      'ascii-font': IntrinsicElements['ascii-font'];
      'tab-select': IntrinsicElements['tab-select'];
      'line-number': IntrinsicElements['line-number'];
      image: IntrinsicElements['image'];
      span: IntrinsicElements['span'];
      br: IntrinsicElements['br'];
      b: IntrinsicElements['b'];
      strong: IntrinsicElements['strong'];
      i: IntrinsicElements['i'];
      em: IntrinsicElements['em'];
      u: IntrinsicElements['u'];
      a: IntrinsicElements['a'];
    }
  }
}

export {};