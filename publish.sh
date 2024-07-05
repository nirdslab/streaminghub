python -m pip install build twine

python -m build streaminghub_curator/
python -m build streaminghub_datamux/
python -m build streaminghub_pydfds/
python -m build streaminghub_plugins/streaminghub_codec_avro/
python -m build streaminghub_plugins/streaminghub_codec_json/
python -m build streaminghub_plugins/streaminghub_codec_msgpack/
python -m build streaminghub_plugins/streaminghub_proxy_empatica_e4/
python -m build streaminghub_plugins/streaminghub_proxy_lsl/
python -m build streaminghub_plugins/streaminghub_proxy_pupil_core/
python -m build streaminghub_plugins/streaminghub_rpc_websocket/

python -m twine check streaminghub_curator/dist/*
python -m twine check streaminghub_datamux/dist/*
python -m twine check streaminghub_pydfds/dist/*
python -m twine check streaminghub_plugins/streaminghub_codec_avro/dist/*
python -m twine check streaminghub_plugins/streaminghub_codec_json/dist/*
python -m twine check streaminghub_plugins/streaminghub_codec_msgpack/dist/*
python -m twine check streaminghub_plugins/streaminghub_proxy_empatica_e4/dist/*
python -m twine check streaminghub_plugins/streaminghub_proxy_lsl/dist/*
python -m twine check streaminghub_plugins/streaminghub_proxy_pupil_core/dist/*
python -m twine check streaminghub_plugins/streaminghub_rpc_websocket/dist/*

python -m twine upload streaminghub_curator/dist/*
python -m twine upload streaminghub_datamux/dist/*
python -m twine upload streaminghub_pydfds/dist/*
python -m twine upload streaminghub_plugins/streaminghub_codec_avro/dist/*
python -m twine upload streaminghub_plugins/streaminghub_codec_json/dist/*
python -m twine upload streaminghub_plugins/streaminghub_codec_msgpack/dist/*
python -m twine upload streaminghub_plugins/streaminghub_proxy_empatica_e4/dist/*
python -m twine upload streaminghub_plugins/streaminghub_proxy_lsl/dist/*
python -m twine upload streaminghub_plugins/streaminghub_proxy_pupil_core/dist/*
python -m twine upload streaminghub_plugins/streaminghub_rpc_websocket/dist/*