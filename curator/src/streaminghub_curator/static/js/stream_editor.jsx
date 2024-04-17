function StreamEditor() {
  const [formData, setFormData] = React.useState({
    name: "",
    description: "",
    unit: "",
    frequency: 0,
    fields: {},
    index: {},
  });

  const handleFieldChange = (category, key, field, value) => {
    setFormData((prevFormData) => ({
      ...prevFormData,
      [category]: {
        ...prevFormData[category],
        [key]: {
          ...prevFormData[category][key],
          [field]: value,
        },
      },
    }));
  };

  const prompt = (text) => {
    return "abc";
  };

  const handleAddField = () => {
    const newFieldKey = prompt("Enter new field key:");
    if (newFieldKey) {
      setFormData((prevFormData) => ({
        ...prevFormData,
        fields: {
          ...prevFormData.fields,
          [newFieldKey]: {
            name: newFieldKey.toLowerCase().replace(/ /g, "_"),
            description: "",
            dtype: "f32",
          },
        },
      }));
    }
  };

  const handleAddIndex = () => {
    const newIndexKey = prompt("Enter new index key:");
    if (newIndexKey) {
      setFormData((prevFormData) => ({
        ...prevFormData,
        index: {
          ...prevFormData.index,
          [newIndexKey]: {
            name: newIndexKey.toLowerCase(),
            description: "",
            dtype: "f32",
          },
        },
      }));
    }
  };

  const createFieldEntry = (ref, key, field) => (
    <div className="row">
      <div className="col-3" key={ref + "_" + key + "_actions"}>
        <div className="input-group">
          <label className="form-label">ID={key}</label>
        </div>
      </div>
      <div className="col-3" key={ref + "_" + key + "_name"}>
        <div className="input-group">
          <label className="form-label">Name</label>
          <input
            type="text"
            className="form-control form-control-sm"
            value={field.name}
            onChange={(e) => handleFieldChange(ref, key, "name", e.target.value)}
          />
        </div>
      </div>
      <div className="col-3" key={ref + "_" + key + "_description"}>
        <div className="input-group">
        <label className="form-label">Description</label>
          <input
            type="text"
            className="form-control form-control-sm"
            value={field.description}
            onChange={(e) => handleFieldChange(ref, key, "description", e.target.value)}
          />
        </div>
      </div>
      <div className="col-3" key={ref + "_" + key + "_dtype"}>
        <div className="input-group">
        <label className="form-label">Dtype</label>
          <select
            type="text"
            className="form-control form-control-sm"
            value={field.dtype}
            onChange={(e) => handleFieldChange(ref, key, "dtype", e.target.value)}
          >
            <option value="f16">float16</option>
            <option value="f32">float32</option>
            <option value="f64">float64</option>
            <option value="i8">int8</option>
            <option value="i16">int16</option>
            <option value="i32">int32</option>
            <option value="u8">uint8</option>
            <option value="u16">uint16</option>
            <option value="u32">uint32</option>
            <option value="byte">byte</option>
          </select>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container">
      <div className="row">
        <div className="col">
          <h2>Add New Stream</h2>
        </div>
      </div>
      <div className="row">
        <div className="col-3">
          <div className="form-floating">
            <input
              type="text"
              className="form-control form-control-sm"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <label>Name:</label>
          </div>
        </div>
        <div className="col-3">
          <div className="form-floating">
            <input
              type="text"
              className="form-control form-control-sm"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            <label>Description:</label>
          </div>
        </div>
        <div className="col-3">
          <div className="form-floating">
            <input
              type="text"
              className="form-control form-control-sm"
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            />
            <label>Unit:</label>
          </div>
        </div>
        <div className="col-3">
          <div className="form-floating">
            <input
              type="number"
              className="form-control form-control-sm"
              value={formData.frequency}
              onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
            />
            <label>Frequency:</label>
          </div>
        </div>
      </div>
      <div className="row">
        <div className="col">
          <h2>Fields:</h2>
          <button type="button" className="btn btn-secondary" onClick={handleAddField}>
            Add Field
          </button>
        </div>
      </div>
      {Object.entries(formData.fields).map(([key, field]) => createFieldEntry("fields", key, field))}
      <div className="row">
        <div className="col">
          <h2>Index:</h2>
          <button type="button" className="btn btn-secondary" onClick={handleAddIndex}>
            Add Index
          </button>
        </div>
      </div>
      {Object.entries(formData.index).map(([key, index]) => createFieldEntry("index", key, index))}
      <div className="row">
        <pre className="col">{JSON.stringify(formData, null, 2)}</pre>
      </div>
    </div>
  );
}
