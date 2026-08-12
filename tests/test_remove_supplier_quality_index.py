from scripts.remove_supplier_quality_index import DEFAULT_COLLECTION, main


def test_remove_script_refuses_non_demo_collection(tmp_path):
    assert (
        main(
            [
                "--persist-path",
                str(tmp_path),
                "--collection",
                "production_documents",
                "--confirm-delete",
                "production_documents",
            ]
        )
        == 1
    )


def test_remove_script_is_read_only_when_index_path_is_absent(tmp_path):
    assert (
        main(
            [
                "--persist-path",
                str(tmp_path / "missing"),
                "--collection",
                DEFAULT_COLLECTION,
            ]
        )
        == 0
    )
