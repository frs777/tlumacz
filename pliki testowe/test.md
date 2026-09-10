# The Future of Local AI Translation

Local language models are becoming increasingly useful for translating technical documentation without sending private documents to external services. A good translation tool must preserve the structure of the original document while translating the human-readable prose accurately and naturally.

## Why structure matters

Markdown files often contain headings, paragraphs, bullet lists, links, inline code, and fenced code blocks. During translation, headings and prose should be translated, while commands, file paths, identifiers, and source code should remain unchanged. The resulting document should still be valid Markdown and should preserve the original organization.

## Example workflow

A typical workflow is simple: select an English Markdown document, choose Polish as the target language, and start the translation. The application divides the document into manageable chunks and sends them to a local model. After each response, the translated chunks are assembled in their original order to create the final document.

The important goal is not merely to produce a Polish version, but to produce one that remains useful to a technical reader. Links must continue to point to the same destinations, code examples must remain executable, and terminology should be consistent throughout the document.

## Performance considerations

Translation speed depends on the model, the available hardware, the size of the prompt, and the number of tokens generated. Keeping unnecessary instructions and repeated context out of the request can reduce processing time, but quality-critical instructions must never be removed simply for the sake of speed.

For this test, the document intentionally contains ordinary technical prose and Markdown structure. It should fit into a single approximately 2000-character chunk so that two translation implementations can be compared under the same conditions.

## Conclusion

A reliable local translator should combin