from pyopencl.version import VERSION, VERSION_STATUS, VERSION_TEXT

import pyopencl._cl as _cl
from pyopencl._cl import *
import inspect as _inspect

CONSTANT_CLASSES = [
        getattr(_cl, name) for name in dir(_cl)
        if _inspect.isclass(getattr(_cl, name))
        and name[0].islower()]

def _add_functionality():
    cls_to_info_cls = {
            _cl.Platform: [
                (_cl.Platform.get_info, _cl.platform_info),
                ],
            _cl.Device: [
                (_cl.Device.get_info, _cl.device_info)
                ], 
            _cl.Context: [
                (_cl.Context.get_info, _cl.context_info),
                ],
            _cl.CommandQueue: [
                (_cl.CommandQueue.get_info, _cl.command_queue_info)
                ],
            _cl.Event: [
                (_cl.Event.get_info, _cl.event_info),
                ],
            _cl.MemoryObject: [
                (MemoryObject.get_info,_cl.mem_info),
                ],
            _cl.Image: [
                (Image.get_image_info, _cl.image_info), 
                (MemoryObject.get_info,_cl.mem_info),
                ],
            _cl.Kernel: [
                (Kernel.get_info, _cl.kernel_info),
                ],
            }

    def to_string(cls, value):
        for name in dir(cls):
            if (not name.startswith("_") and getattr(cls, name) == value):
                return name

        raise ValueError("a name for value %d was not found in %s"
                % (value, cls.__name__))

    for cls in CONSTANT_CLASSES:
        cls.to_string = classmethod(to_string)

    # get_info attributes -----------------------------------------------------
    def make_getattr(info_classes):
        name_to_info = dict(
                (intern(info_name.lower()), (info_method, info_value))
                for info_method, info_class in info_classes[::-1]
                for info_name, info_value in 
                  info_class.__dict__.iteritems()
                if info_name != "to_string" and not info_name.startswith("_")
                )

        def result(self, name):
            try:
                inf_method, inf_attr = name_to_info[name]
            except KeyError:
                raise AttributeError("%s has no attribute '%s'"
                        % (type(self), name))
            else:
                return inf_method(self, inf_attr)

        return result

    for cls, info_classes in cls_to_info_cls.iteritems():
        cls.__getattr__ = make_getattr(info_classes)

    # Program -----------------------------------------------------------------
    def program_getattr(self, attr):
        try:
            pi_attr = getattr(_cl.program_info, attr.upper())
        except AttributeError:
            try:
                knl = Kernel(self, attr)
                # Nvidia does not raise errors even for invalid names,
                # but this will give an error if the kernel is invalid.
                knl.num_args
                return knl
            except LogicError:
                raise AttributeError("'%s' was not found as a program info attribute or as a kernel name"
                        % attr)
        else:
            return self.get_info(pi_attr)

    Program.__getattr__ = program_getattr

    # Event -------------------------------------------------------------------
    class ProfilingInfoGetter:
        def __init__(self, event):
            self.event = event

        def __getattr__(self, name):
            info_cls = _cl.profiling_info

            try:
                inf_attr = getattr(info_cls, name.upper())
            except AttributeError:
                raise AttributeError("%s has no attribute '%s'"
                        % (type(self), name))
            else:
                return self.event.get_profiling_info(inf_attr)

    _cl.Event.profile = property(ProfilingInfoGetter)

    # Kernel ------------------------------------------------------------------
    def kernel_call(self, queue, global_size, *args, **kwargs):
        for i, arg in enumerate(args):
            self.set_arg(i, arg)

        global_offset = kwargs.pop("global_offset", None)
        local_size = kwargs.pop("local_size", None)
        wait_for = kwargs.pop("wait_for", None)

        if kwargs:
            raise TypeError(
                    "Kernel.__call__ recived unexpected keyword arguments: %s"
                    % ", ".join(kwargs.keys()))

        return enqueue_nd_range_kernel(queue, self, global_size, local_size,
                global_offset, wait_for)

    Kernel.__call__ = kernel_call

    # ImageFormat -------------------------------------------------------------
    def image_format_repr(self):
        return "ImageFormat(%s, %s)" % (
                channel_order.to_string(self.channel_order),
                channel_type.to_string(self.channel_data_type))

    ImageFormat.__repr__ = image_format_repr

    # Image -------------------------------------------------------------------
    class ImageInfoGetter:
        def __init__(self, event):
            from warnings import warn
            warn("Image.image.attr is deprecated. "
                    "Use Image.attr directly, instead.")

            self.event = event

        def __getattr__(self, name):
            try:
                inf_attr = getattr(_cl.image_info, name.upper())
            except AttributeError:
                raise AttributeError("%s has no attribute '%s'"
                        % (type(self), name))
            else:
                return self.event.get_image_info(inf_attr)

    _cl.Image.image = property(ImageInfoGetter)

    def event_wait(self):
        wait_for_events([self])
        return self

    Event.wait = event_wait

    if _cl.have_gl():
        def gl_object_get_gl_object(self):
            return self.get_gl_object_info()[1]

        GLBuffer.gl_object = property(gl_object_get_gl_object)
        GLTexture.gl_object = property(gl_object_get_gl_object)

_add_functionality()




# backward compatibility ------------------------------------------------------
def create_image_2d(context, flags, format, width, height, pitch=0, host_buffer=None):
    from warnings import warn
    warn("create_image_2d is deprecated. Use the Image() constructor instead.",
            DeprecationWarning)
    return Image(context, flags, format, (width, height), (pitch,), host_buffer)

def create_image_3d(context, flags, format, width, height, depth,
        row_pitch=0, slice_pitch=0, host_buffer=None):
    from warnings import warn
    warn("create_image_3d is deprecated. Use the Image() constructor instead.",
            DeprecationWarning)
    return Image(context, flags, format, (width, height, depth), 
            (row_pitch, slice_pitch), host_buffer)

def create_program_with_source(context, source):
    from warnings import warn
    warn("create_program_with_source is deprecated. Use the Program() constructor instead.",
            DeprecationWarning)

    return Program(context, source)

def create_program_with_binary(context, devices, binaries):
    from warnings import warn
    warn("create_program_with_binary is deprecated. Use the Program() constructor instead.",
            DeprecationWarning)

    return Program(context, devices, binaries)

def create_buffer(context, flags, size):
    from warnings import warn
    warn("create_buffer is deprecated. Use the Buffer() constructor instead.",
            DeprecationWarning)

    return Buffer(context, flags, size=size)

def create_host_buffer(context, flags, hostbuf):
    from warnings import warn
    warn("create_host_buffer is deprecated. Use the Buffer() constructor instead.",
            DeprecationWarning)

    return Buffer(context, flags, hostbuf=hostbuf)