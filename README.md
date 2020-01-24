<img src="demo/logo2.PNG" width="400" align="center"><br><br><br><br>

# VERSEAGILITY
NLP Toolkit

## Supported Use cases
- Multi-class & multi-label classification
- Named entity recognition
- Question answering

## Live Demo
> http://nlp-demo-app.azurewebsites.net/

## TODO
### Project
- [x] Move to single project config file (for deployment and scoring)
- [ ] Detailed documentation
### Prepare
- [x] source from AML datastore
- [ ] output to AML datastore
### Classification
- [ ] **(IP)** Multi label support
- [ ] integrate handling for larger documents
- [ ] dictionaries for business logic
- [ ] integrate handling for unbalanced datasets
- [ ] upload best model to AML Model
### NER
- [ ] Improve duplicate handling
- [ ] OCR extracted document handling
### Rank
- [ ] **(IP)** Improve answer quality
### Deployment
- [x] Collect, Package and upload assets
- [ ] **(IP)** Param script for deploy (incl language param!)
### Notebooks
- [ ] review prepared data (auto generate after each prepare step)
- [ ] review model results (auto generate after each training step)
- [ ] review model bias (auto generate after each training step)
### DevOps
- [ ] Yaml based infrastructure deployment
- [ ] Integrate with Azure/GitHub DevOps
### Tests
- [ ] integrate testing framework
- [ ] placeholder for custom data loading test
- [ ] placeholder for custom infer test
- [ ] automated benchmarks
### New Features (TBD)
- Summarization
- Deployable feedback loop


# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.