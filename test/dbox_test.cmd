macro read macro=run_tests file="test/run_tests.mac" create_panel=yes


if condition=(eval(db_exists(".gui.main.test_toolbar")))
    interface toolbar delete toolbar_name=.gui.main.test_toolbar
end
interface toolbar create &
    toolbar = .gui.main.test_toolbar &
    location = 0,25 &
    width = 100 &
    height = 25 &
    units = pixel &
    top = no &
    rank = 1

interface toolbar display toolbar=.gui.main.test_toolbar

interface push_button create &
    push_button_name=.gui.main.test_toolbar.run_tests &
    label="Run Tests" &
    location = (eval(nint(.gui.main.width/2))), 4 &
    height = 16 &
    width = 100 &
    units = pixel &
    vert_resizing = attach_bottom &
    horiz_resizing = scale_center &
    commands = "run_tests"
