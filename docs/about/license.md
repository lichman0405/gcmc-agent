# License

GCMC-Agent is licensed under the MIT License.

## MIT License

```
MIT License

Copyright (c) 2026 Shibo Li

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## What This Means

The MIT License is a permissive license that allows you to:

### ✓ Permissions

- **Commercial use**: Use GCMC-Agent in commercial projects
- **Modification**: Modify the source code
- **Distribution**: Distribute the software
- **Private use**: Use for private projects

### ✗ Limitations

- **Liability**: The software is provided "as is" without warranty
- **Warranty**: No warranty is provided

### ℹ Conditions

- **License and copyright notice**: Include the license and copyright notice in all copies

## Third-Party Dependencies

GCMC-Agent uses the following open-source libraries:

- **OpenAI SDK** - Apache 2.0 License
- **LangChain** - MIT License (utilities only)
- **RASPA** - MIT License
- **NumPy** - BSD License
- **Matplotlib** - PSF License
- **Pydantic** - MIT License

See `requirements.txt` in the repository root for complete dependency list.

**Note:** While LangGraph is listed in requirements.txt for compatibility, the current implementation uses a custom ReAct agent framework.

## RASPA License

GCMC-Agent integrates with RASPA (Rapid Simulation Package for Adsorption), which is separately licensed under the MIT License. RASPA is developed by:

- David Dubbeldam (University of Amsterdam)
- Sofia Calero (Eindhoven University of Technology)
- Thijs J.H. Vlugt (Delft University of Technology)

See [RASPA GitHub repository](https://github.com/iRASPA/RASPA2) for details.

## Citation

If you use GCMC-Agent in academic work, please cite:

```bibtex
@software{gcmc_agent_2026,
  title = {GCMC-Agent: Multi-Agent LLM Framework for Molecular Simulation Setup},
  author = {Li, Shibo},
  year = {2026},
  url = {https://github.com/lichman0405/gcmc-agent}
}
```

Also consider citing the original RASPA papers:

```bibtex
@article{dubbeldam2016raspa,
  title={RASPA: molecular simulation software for adsorption and diffusion in flexible nanoporous materials},
  author={Dubbeldam, David and Calero, Sofia and Ellis, Donald E and Snurr, Randall Q},
  journal={Molecular Simulation},
  volume={42},
  number={2},
  pages={81--101},
  year={2016},
  publisher={Taylor \& Francis}
}
```

## Full License Text

The complete license text is available in the `LICENSE` file in the repository root.

## Contact

For licensing questions, please open an issue on GitHub or contact the maintainers.

## Related

- [Contributing Guidelines](../development/contributing.md)
- [Changelog](changelog.md)
